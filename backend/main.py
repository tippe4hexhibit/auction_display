import logging
import logging.config
import numpy as np
from fastapi import FastAPI, WebSocket, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd
import uvicorn
import io

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

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("adbackend")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

sale_program = pd.DataFrame()
buyer_list = pd.DataFrame()
current_lot_index = -1
current_bidders = []
bidders_per_lot = {}
websockets = []

@app.post("/api/upload/sale_program")
async def upload_sale_program(file: UploadFile = File(...)):
    global sale_program
    sale_program = pd.read_excel(file.file)
    sale_program.rename(columns={"Sale #": "LotNumber", "Exhibitor": "StudentName", "Department": "Department"}, inplace=True)
    sale_program.replace({np.nan: None}, inplace=True)
    logger.info(f"Sale program columns after rename: {sale_program.columns.tolist()}")
    await broadcast_state()
    await broadcast_message({"type": "log", "message": f"Sale program uploaded with {len(sale_program)} rows."})
    return {"message": "Sale program uploaded", "rows": len(sale_program)}

@app.post("/api/upload/buyer_list")
async def upload_buyer_list(file: UploadFile = File(...)):
    global buyer_list
    buyer_list = pd.read_excel(file.file)
    buyer_list.replace({np.nan: None}, inplace=True)
    logger.info(f"Buyer list columns: {buyer_list.columns.tolist()}")
    await broadcast_state()
    await broadcast_message({"type": "log", "message": f"Buyer list uploaded with {len(buyer_list)} rows."})
    return {"message": "Buyer list uploaded", "rows": len(buyer_list)}

@app.get("/api/sale")
async def get_sale():
    safe_sale_program = sale_program.replace({np.nan: None})
    return safe_sale_program.to_dict(orient="records")

@app.get("/api/buyers")
async def get_buyers():
    safe_buyer_list = buyer_list.replace({np.nan: None})
    return safe_buyer_list.to_dict(orient="records")

@app.post("/api/lot/next")
async def next_lot():
    global current_lot_index, current_bidders
    if current_lot_index + 1 < len(sale_program):
        current_lot_index += 1
        current_bidders = []
        bidders_per_lot.setdefault(current_lot_index, [])
        await broadcast_state()
        return {"message": "Advanced to next lot"}
    return {"message": "End of lots"}

@app.post("/api/lot/prev")
async def prev_lot():
    global current_lot_index, current_bidders
    if current_lot_index > 0:
        current_lot_index -= 1
        current_bidders = bidders_per_lot.get(current_lot_index, [])
        await broadcast_state()
        return {"message": "Moved to previous lot"}
    return {"message": "Start of lots"}

@app.post("/api/bidder/add/{identifier}")
async def add_bidder(identifier: int):
    global current_bidders
    if identifier not in current_bidders:
        current_bidders.append(identifier)
        bidders_per_lot.setdefault(current_lot_index, []).append(identifier)
        await broadcast_state(bid_update=True)
        await broadcast_message({"type": "log", "message": f"Bidder {identifier} added."})
    return {"message": "Bidder added", "bidders": current_bidders}

@app.get("/api/export/bidders")
async def export_bidders():
    export_data = []
    for lot_idx, bidders in bidders_per_lot.items():
        lot_row = sale_program.iloc[lot_idx]
        export_data.append({
            "LotNumber": lot_row.get("LotNumber"),
            "StudentName": lot_row.get("StudentName"),
            "Department": lot_row.get("Department"),
            "Buyers": ", ".join(str(b) for b in bidders)
        })
    df_export = pd.DataFrame(export_data)
    df_export.replace({np.nan: None}, inplace=True)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_export.to_excel(writer, index=False)
    output.seek(0)
    return StreamingResponse(output, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={"Content-Disposition": "attachment; filename=auction_bidders.xlsx"})

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    websockets.append(ws)
    try:
        while True:
            await ws.receive_text()
    except:
        websockets.remove(ws)

async def broadcast_state(bid_update=False):
    if current_lot_index < 0 or current_lot_index >= len(sale_program):
        return
    lot_row = sale_program.iloc[current_lot_index]
    lot_info = {
        "LotNumber": lot_row.get("LotNumber"),
        "StudentName": lot_row.get("StudentName"),
        "Department": lot_row.get("Department"),
    }
    bidder_info = []
    if current_lot_index in bidders_per_lot:
        for b in bidders_per_lot[current_lot_index]:
            match = buyer_list[buyer_list['Identifier'] == b]
            name = match['Name'].values[0] if not match.empty else "Unknown"
            bidder_info.append({"Identifier": b, "Name": name})
    message_type = "bid_update" if bid_update else "state"
    state = {"type": message_type, "lot": lot_info, "bidders": bidder_info}
    await broadcast_message(state)

async def broadcast_message(message):
    for ws in websockets:
        try:
            await ws.send_json(message)
        except:
            websockets.remove(ws)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
