import logging
from pathlib import Path
import logging.config
import numpy as np
from fastapi import FastAPI, WebSocket, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
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
    SaleProgram, Buyer, BidderLot, AuctionSession, User
)
from auth import authenticate_user, create_access_token, require_auth, create_user, change_user_password, get_all_users, delete_user

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

import os

if os.path.exists("/app/frontend/dist"):
    frontend_dist_path = "/app/frontend/dist"
else:
    frontend_dist_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.exists(frontend_dist_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist_path, "assets")), name="assets")

init_database()

websockets = []

@app.post("/api/auth/login")
async def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return access token."""
    if not authenticate_user(login_request.username, login_request.password, db):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": login_request.username})
    return LoginResponse(access_token=access_token, token_type="bearer")

@app.post("/api/upload/sale_program")
async def upload_sale_program(file: UploadFile = File(...), db: Session = Depends(get_db), user: dict = Depends(require_auth)):
    df = pd.read_excel(file.file)
    df.rename(columns={"Sale #": "LotNumber", "Exhibitor": "StudentName", "Department": "Department"}, inplace=True)
    df.replace({np.nan: None}, inplace=True)
    
    existing_lots = {lot.lot_number: lot for lot in db.query(SaleProgram).all()}
    
    updated_count = 0
    added_count = 0
    
    for _, row in df.iterrows():
        lot_number_str = str(row.get("LotNumber", ""))
        student_name_str = str(row.get("StudentName", ""))
        department_str = str(row.get("Department", ""))
        
        if lot_number_str in existing_lots:
            existing_lot = existing_lots[lot_number_str]
            if (existing_lot.student_name != student_name_str or 
                existing_lot.department != department_str):
                existing_lot.student_name = student_name_str
                existing_lot.department = department_str
                updated_count += 1
        else:
            lot = SaleProgram(
                lot_number=lot_number_str,
                student_name=student_name_str,
                department=department_str
            )
            db.add(lot)
            added_count += 1
    
    db.commit()
    message = f"Sale program processed: {added_count} added, {updated_count} updated"
    logger.info(message)
    await broadcast_state(db)
    await broadcast_message({"type": "log", "message": message})
    return {"message": message, "added": added_count, "updated": updated_count}

@app.post("/api/upload/buyer_list")
async def upload_buyer_list(file: UploadFile = File(...), db: Session = Depends(get_db), user: dict = Depends(require_auth)):
    df = pd.read_excel(file.file)
    df.replace({np.nan: None}, inplace=True)
    
    existing_buyers = {buyer.identifier: buyer for buyer in db.query(Buyer).all()}
    
    updated_count = 0
    added_count = 0
    
    for _, row in df.iterrows():
        identifier_value = row.get("Identifier")
        if identifier_value is None or pd.isna(identifier_value):
            identifier_value = 0
        
        identifier_int = int(identifier_value)
        name_str = str(row.get("Name", ""))
        
        if identifier_int in existing_buyers:
            existing_buyer = existing_buyers[identifier_int]
            if existing_buyer.name != name_str:
                existing_buyer.name = name_str
                updated_count += 1
        else:
            buyer = Buyer(
                identifier=identifier_int,
                name=name_str
            )
            db.add(buyer)
            added_count += 1
    
    db.commit()
    message = f"Buyer list processed: {added_count} added, {updated_count} updated"
    logger.info(message)
    await broadcast_state(db)
    await broadcast_message({"type": "log", "message": message})
    return {"message": message, "added": added_count, "updated": updated_count}

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
    
    lot_info = {
        "LotNumber": current_lot.lot_number,
        "StudentName": current_lot.student_name,
        "Department": current_lot.department
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
    session = get_or_create_session(db)
    total_lots = db.query(SaleProgram).count()
    
    if session.current_lot_index + 1 < total_lots:
        session.current_lot_index += 1
        db.commit()
        
        await broadcast_state(db)
        return {"message": "Advanced to next lot"}
    return {"message": "End of lots"}

@app.post("/api/lot/prev")
async def prev_lot(db: Session = Depends(get_db), user: dict = Depends(require_auth)):
    session = get_or_create_session(db)
    
    if session.current_lot_index > 0:
        session.current_lot_index -= 1
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

class CreateUserRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    username: str
    new_password: str

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

@app.get("/api/users")
async def get_users(db: Session = Depends(get_db), user: dict = Depends(require_auth)):
    """Get all users."""
    users = get_all_users(db)
    return [{"username": u.username, "created_at": u.created_at} for u in users]

@app.post("/api/users")
async def create_new_user(request: CreateUserRequest, db: Session = Depends(get_db), user: dict = Depends(require_auth)):
    """Create a new admin user."""
    if create_user(request.username, request.password, db):
        await broadcast_message({"type": "log", "message": f"Created new admin user: {request.username}"})
        return {"message": f"User {request.username} created successfully"}
    else:
        raise HTTPException(status_code=400, detail="Username already exists")

@app.post("/api/users/change-password")
async def change_password(request: ChangePasswordRequest, db: Session = Depends(get_db), user: dict = Depends(require_auth)):
    """Change password for a user."""
    if change_user_password(request.username, request.new_password, db):
        await broadcast_message({"type": "log", "message": f"Password changed for user: {request.username}"})
        return {"message": f"Password changed for {request.username}"}
    else:
        raise HTTPException(status_code=404, detail="User not found")

@app.delete("/api/users/{username}")
async def delete_user_endpoint(username: str, db: Session = Depends(get_db), user: dict = Depends(require_auth)):
    """Delete a user."""
    if delete_user(username, db):
        await broadcast_message({"type": "log", "message": f"Deleted user: {username}"})
        return {"message": f"User {username} deleted successfully"}
    else:
        raise HTTPException(status_code=400, detail="Cannot delete user (user not found or is default admin)")

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
    session = get_or_create_session(db)
    
    current_lot = db.query(SaleProgram).offset(session.current_lot_index).first()
    if not current_lot:
        return
    
    lot_info = {
        "LotNumber": current_lot.lot_number,
        "StudentName": current_lot.student_name,
        "Department": current_lot.department
    }
    
    bidders = db.query(BidderLot).filter(BidderLot.lot_id == current_lot.id).all()
    bidder_info = []
    for bidder in bidders:
        buyer = db.query(Buyer).filter(Buyer.id == bidder.buyer_id).first()
        if buyer:
            bidder_info.append({"Identifier": buyer.identifier, "Name": buyer.name})
    
    message_type = "bid_update" if bid_update else "state"
    state = {"type": message_type, "lot": lot_info, "bidders": bidder_info}
    await broadcast_message(state)

async def broadcast_message(message):
    for ws in websockets:
        try:
            await ws.send_json(message)
        except:
            websockets.remove(ws)

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve the SPA for all non-API routes"""
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not Found")
    
    if os.path.exists("/app/frontend/dist"):
        frontend_dist_path = "/app/frontend/dist"
    else:
        frontend_dist_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
    
    return FileResponse(os.path.join(frontend_dist_path, "index.html"))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
