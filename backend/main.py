import logging
from pathlib import Path
import logging.config
import numpy as np
from fastapi import FastAPI, WebSocket, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import uvicorn
import io
import os
import shutil
from pathlib import Path
from sqlalchemy.orm import Session
from database import (
    init_database, get_db, get_or_create_session,
    SaleProgram, Buyer, BidderLot, AuctionSession, LotImage, PacingStats
)
from auth import authenticate_user, create_access_token, require_auth

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"default": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
    "loggers": {
        "uvicorn": {"handlers": ["console"], "level": "INFO"},
        "uvicorn.error": {"handlers": ["console"], "level": "ERROR"},
        "uvicorn.access": {"handlers": ["console"], "level": "INFO"},
        "adbackend": {"handlers": ["console"], "level": "INFO"}
    }
}

working_dir = os.path.dirname(__file__)

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("adbackend")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.mount("/images", StaticFiles(directory= working_dir / Path("data/images")), name="images")

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

init_database()

websockets = []

@app.post("/api/auth/login")
async def login(login_request: LoginRequest):
    """Authenticate user and return access token."""
    if not authenticate_user(login_request.username, login_request.password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": login_request.username})
    return LoginResponse(access_token=access_token, token_type="bearer")

@app.post("/api/upload/sale_program")
async def upload_sale_program(file: UploadFile = File(...), db: Session = Depends(get_db), user: dict = Depends(require_auth)):
    db.query(SaleProgram).delete()
    db.commit()
    
    df = pd.read_excel(file.file)
    df.rename(columns={"Sale #": "LotNumber", "Exhibitor": "StudentName", "Department": "Department"}, inplace=True)
    df.replace({np.nan: None}, inplace=True)
    
    for _, row in df.iterrows():
        lot = SaleProgram(
            lot_number=str(row.get("LotNumber", "")),
            student_name=str(row.get("StudentName", "")),
            department=str(row.get("Department", ""))
        )
        db.add(lot)
    
    db.commit()
    logger.info(f"Sale program uploaded with {len(df)} rows.")
    await broadcast_state(db)
    await broadcast_message({"type": "log", "message": f"Sale program uploaded with {len(df)} rows."})
    return {"message": "Sale program uploaded", "rows": len(df)}

@app.post("/api/upload/buyer_list")
async def upload_buyer_list(file: UploadFile = File(...), db: Session = Depends(get_db), user: dict = Depends(require_auth)):
    db.query(Buyer).delete()
    db.commit()
    
    df = pd.read_excel(file.file)
    df.replace({np.nan: None}, inplace=True)
    
    for _, row in df.iterrows():
        identifier_value = row.get("Identifier")
        if identifier_value is None or pd.isna(identifier_value):
            identifier_value = 0
        
        buyer = Buyer(
            identifier=int(identifier_value),
            name=str(row.get("Name", ""))
        )
        db.add(buyer)
    
    db.commit()
    logger.info(f"Buyer list uploaded with {len(df)} rows.")
    await broadcast_state(db)
    await broadcast_message({"type": "log", "message": f"Buyer list uploaded with {len(df)} rows."})
    return {"message": "Buyer list uploaded", "rows": len(df)}

@app.get("/api/sale")
async def get_sale(db: Session = Depends(get_db)):
    lots = db.query(SaleProgram).all()
    return [
        {
            "LotNumber": lot.lot_number,
            "StudentName": lot.student_name,
            "Department": lot.department
        }
        for lot in lots
    ]

@app.get("/api/buyers")
async def get_buyers(db: Session = Depends(get_db)):
    buyers = db.query(Buyer).all()
    return [
        {
            "Identifier": buyer.identifier,
            "Name": buyer.name
        }
        for buyer in buyers
    ]

@app.get("/api/state")
async def get_current_state(db: Session = Depends(get_db)):
    session = get_or_create_session(db)
    
    current_lot = db.query(SaleProgram).offset(session.current_lot_index).first()
    if not current_lot:
        return {"lot": None, "bidders": []}
    
    lot_image = db.query(LotImage).filter(LotImage.lot_id == current_lot.id).first()
    image_url = lot_image.url if lot_image else None
    
    lot_info = {
        "LotNumber": current_lot.lot_number,
        "StudentName": current_lot.student_name,
        "Department": current_lot.department,
        "image_url": image_url
    }
    
    bidders = db.query(BidderLot).filter(BidderLot.lot_id == current_lot.id).all()
    bidder_info = []
    for bidder in bidders:
        buyer = db.query(Buyer).filter(Buyer.id == bidder.buyer_id).first()
        if buyer:
            bidder_info.append({"Identifier": buyer.identifier, "Name": buyer.name})
    
    return {"lot": lot_info, "bidders": bidder_info}

@app.post("/api/lot/next")
async def next_lot(db: Session = Depends(get_db), user: dict = Depends(require_auth)):
    from datetime import datetime
    session = get_or_create_session(db)
    total_lots = db.query(SaleProgram).count()
    
    if session.current_lot_index >= 0:
        current_lot = db.query(SaleProgram).offset(session.current_lot_index).first()
        if current_lot:
            pacing_stat = db.query(PacingStats).filter(
                PacingStats.lot_index == session.current_lot_index,
                PacingStats.end_time.is_(None)
            ).first()
            if pacing_stat:
                pacing_stat.end_time = datetime.utcnow()
                pacing_stat.duration_seconds = int((pacing_stat.end_time - pacing_stat.start_time).total_seconds())
    
    if session.current_lot_index + 1 < total_lots:
        session.current_lot_index += 1
        
        new_pacing_stat = PacingStats(
            lot_index=session.current_lot_index,
            start_time=datetime.utcnow()
        )
        db.add(new_pacing_stat)
        db.commit()
        
        await broadcast_state(db)
        return {"message": "Advanced to next lot"}
    return {"message": "End of lots"}

@app.post("/api/lot/prev")
async def prev_lot(db: Session = Depends(get_db), user: dict = Depends(require_auth)):
    from datetime import datetime
    session = get_or_create_session(db)
    
    if session.current_lot_index > 0:
        pacing_stat = db.query(PacingStats).filter(
            PacingStats.lot_index == session.current_lot_index,
            PacingStats.end_time.is_(None)
        ).first()
        if pacing_stat:
            pacing_stat.end_time = datetime.utcnow()
            pacing_stat.duration_seconds = int((pacing_stat.end_time - pacing_stat.start_time).total_seconds())
        
        session.current_lot_index -= 1
        
        new_pacing_stat = PacingStats(
            lot_index=session.current_lot_index,
            start_time=datetime.utcnow()
        )
        db.add(new_pacing_stat)
        db.commit()
        
        await broadcast_state(db)
        return {"message": "Moved to previous lot"}
    return {"message": "Start of lots"}

@app.post("/api/bidder/add/{identifier}")
async def add_bidder(identifier: int, db: Session = Depends(get_db), user: dict = Depends(require_auth)):
    session = get_or_create_session(db)
    
    current_lot = db.query(SaleProgram).offset(session.current_lot_index).first()
    if not current_lot:
        raise HTTPException(status_code=404, detail="No current lot")
    
    buyer = db.query(Buyer).filter(Buyer.identifier == identifier).first()
    if not buyer:
        buyer = Buyer(identifier=identifier, name=f"Buyer {identifier}")
        db.add(buyer)
        db.commit()
        db.refresh(buyer)
    
    existing_bid = db.query(BidderLot).filter(
        BidderLot.lot_id == current_lot.id,
        BidderLot.buyer_id == buyer.id
    ).first()
    
    if not existing_bid:
        bid = BidderLot(
            lot_id=current_lot.id,
            buyer_id=buyer.id,
            lot_index=session.current_lot_index
        )
        db.add(bid)
        db.commit()
        
        await broadcast_state(db, bid_update=True)
        await broadcast_message({"type": "log", "message": f"Bidder {identifier} added."})
    
    return {"message": "Bidder added"}

@app.get("/api/export/bidders")
async def export_bidders(db: Session = Depends(get_db), user: dict = Depends(require_auth)):
    export_data = []
    lots = db.query(SaleProgram).all()
    
    for lot in lots:
        bidders = db.query(BidderLot).filter(BidderLot.lot_id == lot.id).all()
        buyer_names = []
        for bidder in bidders:
            buyer = db.query(Buyer).filter(Buyer.id == bidder.buyer_id).first()
            if buyer:
                buyer_names.append(str(buyer.identifier))
        
        export_data.append({
            "LotNumber": lot.lot_number,
            "StudentName": lot.student_name,
            "Department": lot.department,
            "Buyers": ", ".join(buyer_names)
        })
    
    df_export = pd.DataFrame(export_data)
    df_export.replace({np.nan: None}, inplace=True)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_export.to_excel(writer, index=False)
    output.seek(0)
    return StreamingResponse(output, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={"Content-Disposition": "attachment; filename=auction_bidders.xlsx"})

@app.post("/api/lot/{lot_number}/image")
async def upload_lot_image(lot_number: str, file: UploadFile = File(...), db: Session = Depends(get_db), user: dict = Depends(require_auth)):
    """Upload an image for a specific lot."""
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")
    
    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size: {MAX_IMAGE_SIZE // (1024*1024)}MB")
    
    lot = db.query(SaleProgram).filter(SaleProgram.lot_number == lot_number).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    
    safe_filename = f"lot_{lot_number}_{int(pd.Timestamp.now().timestamp())}{file_extension}"
    file_path = Path("data/images") / safe_filename
    
    with open(file_path, "wb") as f:
        f.write(contents)
    
    existing_image = db.query(LotImage).filter(LotImage.lot_id == lot.id).first()
    if existing_image:
        old_path = Path("data/images") / existing_image.filename
        if old_path.exists():
            old_path.unlink()
        existing_image.filename = safe_filename
        existing_image.url = f"/images/{safe_filename}"
    else:
        lot_image = LotImage(
            lot_id=lot.id,
            filename=safe_filename,
            url=f"/images/{safe_filename}"
        )
        db.add(lot_image)
    
    db.commit()
    
    await broadcast_state(db)
    await broadcast_message({"type": "log", "message": f"Image uploaded for lot {lot_number}"})
    
    return {"message": "Image uploaded successfully", "url": f"/images/{safe_filename}"}

@app.post("/api/bidder/undo")
async def undo_bidder(db: Session = Depends(get_db), user: dict = Depends(require_auth)):
    """Remove the last bidder from the current lot."""
    session = get_or_create_session(db)
    
    current_lot = db.query(SaleProgram).offset(session.current_lot_index).first()
    if not current_lot:
        raise HTTPException(status_code=404, detail="No current lot")
    
    last_bidder = db.query(BidderLot).filter(
        BidderLot.lot_id == current_lot.id
    ).order_by(BidderLot.created_at.desc()).first()
    
    if not last_bidder:
        raise HTTPException(status_code=404, detail="No bidders to undo for this lot")
    
    buyer = db.query(Buyer).filter(Buyer.id == last_bidder.buyer_id).first()
    buyer_identifier = buyer.identifier if buyer else "Unknown"
    
    db.delete(last_bidder)
    db.commit()
    
    await broadcast_state(db)
    await broadcast_message({"type": "log", "message": f"Undid bidder {buyer_identifier} from lot {current_lot.lot_number}"})
    
    return {"message": f"Undid bidder {buyer_identifier}"}

class MergeRequest(BaseModel):
    source_identifier: int
    target_identifier: int

@app.post("/api/bidder/merge")
async def merge_bidders(merge_request: MergeRequest, db: Session = Depends(get_db), user: dict = Depends(require_auth)):
    """Merge two bidder records."""
    source_buyer = db.query(Buyer).filter(Buyer.identifier == merge_request.source_identifier).first()
    target_buyer = db.query(Buyer).filter(Buyer.identifier == merge_request.target_identifier).first()
    
    if not source_buyer:
        raise HTTPException(status_code=404, detail=f"Source bidder {merge_request.source_identifier} not found")
    if not target_buyer:
        raise HTTPException(status_code=404, detail=f"Target bidder {merge_request.target_identifier} not found")
    
    if source_buyer.id == target_buyer.id:
        raise HTTPException(status_code=400, detail="Cannot merge bidder with itself")
    
    source_bids = db.query(BidderLot).filter(BidderLot.buyer_id == source_buyer.id).all()
    
    for bid in source_bids:
        existing_target_bid = db.query(BidderLot).filter(
            BidderLot.lot_id == bid.lot_id,
            BidderLot.buyer_id == target_buyer.id
        ).first()
        
        if existing_target_bid:
            db.delete(bid)
        else:
            bid.buyer_id = target_buyer.id
    
    db.delete(source_buyer)
    db.commit()
    
    await broadcast_state(db)
    await broadcast_message({"type": "log", "message": f"Merged bidder {merge_request.source_identifier} into {merge_request.target_identifier}"})
    
    return {"message": f"Merged bidder {merge_request.source_identifier} into {merge_request.target_identifier}"}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    websockets.append(ws)
    try:
        while True:
            await ws.receive_text()
    except:
        websockets.remove(ws)

async def broadcast_state(db: Session, bid_update=False):
    from datetime import datetime
    session = get_or_create_session(db)
    
    current_lot = db.query(SaleProgram).offset(session.current_lot_index).first()
    if not current_lot:
        return
    
    lot_image = db.query(LotImage).filter(LotImage.lot_id == current_lot.id).first()
    image_url = lot_image.url if lot_image else None
    
    current_pacing = db.query(PacingStats).filter(
        PacingStats.lot_index == session.current_lot_index,
        PacingStats.end_time.is_(None)
    ).first()
    
    pacing_info = None
    if current_pacing:
        current_duration = int((datetime.utcnow() - current_pacing.start_time).total_seconds())
        
        completed_stats = db.query(PacingStats).filter(
            PacingStats.duration_seconds.isnot(None)
        ).all()
        
        if completed_stats:
            avg_duration = sum(stat.duration_seconds for stat in completed_stats) / len(completed_stats)
            if current_duration > avg_duration * 1.5:
                suggestion = "Consider speeding up - lot is taking longer than average"
            elif current_duration < avg_duration * 0.5:
                suggestion = "Consider slowing down - lot is moving faster than average"
            else:
                suggestion = "Pacing looks good"
        else:
            suggestion = "Building pacing baseline"
        
        pacing_info = {
            "current_duration": current_duration,
            "average_duration": int(avg_duration) if completed_stats else None,
            "suggestion": suggestion
        }
    
    lot_info = {
        "LotNumber": current_lot.lot_number,
        "StudentName": current_lot.student_name,
        "Department": current_lot.department,
        "image_url": image_url
    }
    
    bidders = db.query(BidderLot).filter(BidderLot.lot_id == current_lot.id).all()
    bidder_info = []
    for bidder in bidders:
        buyer = db.query(Buyer).filter(Buyer.id == bidder.buyer_id).first()
        if buyer:
            bidder_info.append({"Identifier": buyer.identifier, "Name": buyer.name})
    
    message_type = "bid_update" if bid_update else "state"
    state = {"type": message_type, "lot": lot_info, "bidders": bidder_info, "pacing": pacing_info}
    await broadcast_message(state)

async def broadcast_message(message):
    for ws in websockets:
        try:
            await ws.send_json(message)
        except:
            websockets.remove(ws)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
