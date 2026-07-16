import asyncio
import base64
import hashlib
import logging
import os
from datetime import datetime, timedelta

from cryptography.fernet import Fernet, InvalidToken
from fairentry_api import FairEntryClient, FairEntryError

from database import Buyer, FairEntrySettings, SessionLocal, get_or_create_fairentry_settings
from ws_manager import broadcast_message

logger = logging.getLogger("adbackend")

FAILURE_THRESHOLD = 3
SYNC_CHECK_TICK_SECONDS = 30

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
_FERNET = Fernet(base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode("utf-8")).digest()))


def encrypt_password(plain: str) -> str:
    return _FERNET.encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_password(cipher: str) -> str:
    return _FERNET.decrypt(cipher.encode("utf-8")).decode("utf-8")


def settings_to_dict(settings: FairEntrySettings) -> dict:
    return {
        "username": settings.username,
        "fair_title": settings.fair_title,
        "sync_enabled": settings.sync_enabled,
        "sync_interval_minutes": settings.sync_interval_minutes,
        # last_sync_at is stored naive UTC (datetime.utcnow()); tag it explicitly
        # so the browser's Date parser treats it as UTC rather than local time,
        # which lets toLocaleString() convert it to the viewer's timezone correctly.
        "last_sync_at": settings.last_sync_at.isoformat() + "Z" if settings.last_sync_at else None,
        "last_sync_status": settings.last_sync_status,
        "last_sync_message": settings.last_sync_message,
        "consecutive_failures": settings.consecutive_failures,
        "has_password": bool(settings.password_encrypted),
    }


_sync_lock = asyncio.Lock()


async def perform_sync(db) -> dict:
    """Fetch the buyer list from FairEntry and upsert it into the Buyer table.

    Reads credentials/fair title fresh from the DB every call (rather than
    reusing a persisted client/session), so edits made in the admin UI take
    effect on the very next sync without a restart.
    """
    async with _sync_lock:
        return await _perform_sync_locked(db)


async def _perform_sync_locked(db) -> dict:
    settings = get_or_create_fairentry_settings(db)

    if not (settings.username and settings.password_encrypted and settings.fair_title):
        result = {"status": "skipped", "message": "FairEntry credentials not configured"}
        await _broadcast_status(db, settings, result)
        return result

    try:
        password = decrypt_password(settings.password_encrypted)
    except InvalidToken:
        result = {"status": "error", "message": "Stored password could not be decrypted; re-enter it"}
        await _record_failure(db, settings, result["message"])
        await _broadcast_status(db, settings, result)
        return result

    try:
        client = FairEntryClient()
        await asyncio.to_thread(client.authenticate, settings.username, password, settings.fair_title)
        fe_buyers = await asyncio.to_thread(client.get_buyers, True)
    except FairEntryError as e:
        result = {"status": "error", "message": str(e)}
        await _record_failure(db, settings, result["message"])
        await _broadcast_status(db, settings, result)
        return result

    existing_buyers = {buyer.identifier: buyer for buyer in db.query(Buyer).all()}
    added_count = 0
    updated_count = 0
    skipped = []

    for fe_buyer in fe_buyers:
        try:
            identifier_int = int(fe_buyer.identifier)
        except (TypeError, ValueError):
            skipped.append(fe_buyer.identifier)
            continue

        name_str = fe_buyer.name or ""

        if identifier_int in existing_buyers:
            existing_buyer = existing_buyers[identifier_int]
            if existing_buyer.name != name_str:
                existing_buyer.name = name_str
                updated_count += 1
        else:
            db.add(Buyer(identifier=identifier_int, name=name_str))
            added_count += 1

    message = f"FairEntry sync: {added_count} added, {updated_count} updated"
    if skipped:
        message += f" ({len(skipped)} buyer(s) skipped - non-numeric identifier)"
        logger.warning(f"FairEntry sync skipped non-numeric identifiers: {skipped}")

    settings.last_sync_at = datetime.utcnow()
    settings.last_sync_status = "success"
    settings.last_sync_message = message
    settings.consecutive_failures = 0
    db.commit()

    logger.info(message)
    result = {"status": "success", "message": message, "added": added_count, "updated": updated_count}
    await _broadcast_status(db, settings, result)
    return result


async def _record_failure(db, settings: FairEntrySettings, error_message: str):
    settings.last_sync_at = datetime.utcnow()
    settings.last_sync_status = "error"
    settings.consecutive_failures = (settings.consecutive_failures or 0) + 1

    if settings.consecutive_failures >= FAILURE_THRESHOLD:
        settings.sync_enabled = False
        settings.last_sync_message = (
            f"{error_message} (auto-disabled after {FAILURE_THRESHOLD} consecutive failures)"
        )
    else:
        settings.last_sync_message = error_message

    db.commit()
    logger.error(f"FairEntry sync failed: {settings.last_sync_message}")


async def _broadcast_status(db, settings: FairEntrySettings, result: dict):
    await broadcast_message({"type": "fairentry_status", **settings_to_dict(settings)})
    if result.get("status") == "success":
        await broadcast_message({"type": "buyers_updated"})
    if result.get("status") in ("success", "error"):
        await broadcast_message({"type": "log", "message": result["message"]})


async def fairentry_sync_loop():
    """Background task: periodically checks whether an auto-sync is due."""
    while True:
        await asyncio.sleep(SYNC_CHECK_TICK_SECONDS)
        db = SessionLocal()
        try:
            settings = get_or_create_fairentry_settings(db)
            if not settings.sync_enabled:
                continue

            interval = timedelta(minutes=settings.sync_interval_minutes or 15)
            if settings.last_sync_at and datetime.utcnow() - settings.last_sync_at < interval:
                continue

            await perform_sync(db)
        except Exception:
            logger.exception("Unexpected error in FairEntry sync loop")
        finally:
            db.close()
