import logging

logger = logging.getLogger("adbackend")

websockets = []


async def broadcast_message(message):
    logger.info(f"Broadcasting type={message.get('type')} to {len(websockets)} client(s)")
    for ws in list(websockets):
        try:
            await ws.send_json(message)
        except Exception as e:
            logger.info(f"Broadcast send failed ({e!r}), dropping client")
            websockets.remove(ws)
