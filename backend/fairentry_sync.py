import asyncio
import base64
import hashlib
import logging
import os
from datetime import datetime, timedelta

from cryptography.fernet import Fernet, InvalidToken
from fairentry_api import FairEntryClient, FairEntryError

from database import (
    Buyer, SaleProgram, BidderLot,
    FairEntryConnection, FairEntrySyncStatus, FairEntrySaleOrderOption,
    SessionLocal, clamp_current_lot_index,
    get_or_create_fairentry_connection, get_or_create_fairentry_sync_status,
    get_or_create_session,
)
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


def connection_to_dict(connection: FairEntryConnection) -> dict:
    return {
        "username": connection.username,
        "fair_title": connection.fair_title,
        "has_password": bool(connection.password_encrypted),
    }


def status_to_dict(status: FairEntrySyncStatus) -> dict:
    return {
        "target": status.target,
        "sync_enabled": status.sync_enabled,
        "sync_interval_minutes": status.sync_interval_minutes,
        # last_sync_at is stored naive UTC (datetime.utcnow()); tag it explicitly
        # so the browser's Date parser treats it as UTC rather than local time,
        # which lets toLocaleString() convert it to the viewer's timezone correctly.
        "last_sync_at": status.last_sync_at.isoformat() + "Z" if status.last_sync_at else None,
        "last_sync_status": status.last_sync_status,
        "last_sync_message": status.last_sync_message,
        "consecutive_failures": status.consecutive_failures,
        "selected_sale_order_id": status.selected_sale_order_id,
        "selected_sale_order_name": status.selected_sale_order_name,
    }


def sale_order_option_to_dict(option) -> dict:
    return {"id": option.id, "name": option.name, "entry_count": option.entry_count}


class _NotConfigured(Exception):
    pass


async def _authenticate(connection: FairEntryConnection) -> FairEntryClient:
    """Build and log in a FairEntryClient using the shared connection
    credentials, reading them fresh from the DB every call so edits made in
    Preferences take effect on the very next sync without a restart.

    Raises _NotConfigured if credentials are incomplete, or FairEntryError
    (from the underlying client) if login itself fails.
    """
    if not (connection.username and connection.password_encrypted and connection.fair_title):
        raise _NotConfigured("FairEntry credentials not configured")

    try:
        password = decrypt_password(connection.password_encrypted)
    except InvalidToken:
        raise FairEntryError("Stored password could not be decrypted; re-enter it in Preferences")

    client = FairEntryClient()
    await asyncio.to_thread(client.authenticate, connection.username, password, connection.fair_title)
    return client


_sync_locks = {"buyers": asyncio.Lock(), "sale": asyncio.Lock()}


async def _record_failure(db, status: FairEntrySyncStatus, error_message: str):
    status.last_sync_at = datetime.utcnow()
    status.last_sync_status = "error"
    status.consecutive_failures = (status.consecutive_failures or 0) + 1

    if status.consecutive_failures >= FAILURE_THRESHOLD:
        status.sync_enabled = False
        status.last_sync_message = (
            f"{error_message} (auto-disabled after {FAILURE_THRESHOLD} consecutive failures)"
        )
    else:
        status.last_sync_message = error_message

    db.commit()
    logger.error(f"FairEntry {status.target} sync failed: {status.last_sync_message}")


async def _broadcast_status(status: FairEntrySyncStatus, result: dict, extra_type: str = None):
    await broadcast_message({"type": f"fairentry_{status.target}_sync_status", **status_to_dict(status)})
    if extra_type and result.get("status") == "success":
        await broadcast_message({"type": extra_type})
    if result.get("status") in ("success", "error"):
        await broadcast_message({"type": "log", "message": result["message"]})


async def perform_buyer_sync(db) -> dict:
    """Fetch the buyer list from FairEntry and upsert it into the Buyer table.
    Additive only - never deletes a buyer that's disappeared upstream."""
    async with _sync_locks["buyers"]:
        return await _perform_buyer_sync_locked(db)


async def _perform_buyer_sync_locked(db) -> dict:
    connection = get_or_create_fairentry_connection(db)
    status = get_or_create_fairentry_sync_status(db, "buyers")

    try:
        client = await _authenticate(connection)
    except _NotConfigured as e:
        result = {"status": "skipped", "message": str(e)}
        await _broadcast_status(status, result)
        return result
    except FairEntryError as e:
        result = {"status": "error", "message": str(e)}
        await _record_failure(db, status, result["message"])
        await _broadcast_status(status, result)
        return result

    try:
        fe_buyers = await asyncio.to_thread(client.get_buyers, True)
    except FairEntryError as e:
        result = {"status": "error", "message": str(e)}
        await _record_failure(db, status, result["message"])
        await _broadcast_status(status, result)
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

    message = f"FairEntry buyer sync: {added_count} added, {updated_count} updated"
    if skipped:
        message += f" ({len(skipped)} buyer(s) skipped - non-numeric identifier)"
        logger.warning(f"FairEntry buyer sync skipped non-numeric identifiers: {skipped}")

    status.last_sync_at = datetime.utcnow()
    status.last_sync_status = "success"
    status.last_sync_message = message
    status.consecutive_failures = 0
    db.commit()

    logger.info(message)
    result = {"status": "success", "message": message, "added": added_count, "updated": updated_count}
    await _broadcast_status(status, result, extra_type="buyers_updated")
    return result


async def perform_sale_sync(db) -> dict:
    """Fetch the selected Sale Order from FairEntry and mirror it into the
    SaleProgram table. Unlike buyer sync this is a full replace, not an
    upsert: the Sale List must end up 100% matching the source and strictly
    ordered by lot number, so stale/removed/renumbered lots can't linger."""
    async with _sync_locks["sale"]:
        return await _perform_sale_sync_locked(db)


async def _perform_sale_sync_locked(db) -> dict:
    connection = get_or_create_fairentry_connection(db)
    status = get_or_create_fairentry_sync_status(db, "sale")

    try:
        client = await _authenticate(connection)
    except _NotConfigured as e:
        result = {"status": "skipped", "message": str(e)}
        await _broadcast_status(status, result)
        return result
    except FairEntryError as e:
        result = {"status": "error", "message": str(e)}
        await _record_failure(db, status, result["message"])
        await _broadcast_status(status, result)
        return result

    if not status.selected_sale_order_id:
        try:
            sale_orders = await asyncio.to_thread(client.get_sale_orders, True)
        except FairEntryError as e:
            result = {"status": "error", "message": str(e)}
            await _record_failure(db, status, result["message"])
            await _broadcast_status(status, result)
            return result

        if len(sale_orders) == 1:
            status.selected_sale_order_id = sale_orders[0].id
            status.selected_sale_order_name = sale_orders[0].name
            db.commit()
        else:
            message = (
                "No Sale Orders found in FairEntry" if not sale_orders
                else "Multiple Sale Orders exist — select one in the Sale List tab"
            )
            result = {"status": "skipped", "message": message}
            await _broadcast_status(status, result)
            return result

    try:
        detail = await asyncio.to_thread(client.get_sale_order, status.selected_sale_order_id, True)
    except FairEntryError as e:
        result = {"status": "error", "message": str(e)}
        await _record_failure(db, status, result["message"])
        await _broadcast_status(status, result)
        return result

    entries = detail.entries_sorted_by_sale_number()
    sale_order_id = status.selected_sale_order_id

    # Full replace, scoped to this Sale Order only - a sync is a mirror of
    # the source, not a merge, but other Sale Orders' cached rows are left
    # alone so switching the dropdown selection doesn't need a re-sync.
    stale_lot_ids = [
        row.id for row in db.query(SaleProgram.id)
        .filter(SaleProgram.sale_order_id == sale_order_id).all()
    ]
    if stale_lot_ids:
        db.query(BidderLot).filter(BidderLot.lot_id.in_(stale_lot_ids)).delete(synchronize_session=False)
        db.query(SaleProgram).filter(SaleProgram.id.in_(stale_lot_ids)).delete(synchronize_session=False)

    for index, entry in enumerate(entries):
        db.add(SaleProgram(
            lot_number=str(entry.sale_number),
            student_name=entry.exhibitor_name or "",
            department=entry.department_name or "",
            sort_order=index,
            fairentry_entry_id=entry.id,
            sale_order_id=sale_order_id,
        ))

    session = get_or_create_session(db)
    clamp_current_lot_index(session, len(entries))

    message = f"FairEntry sale sync: {len(entries)} lot(s) loaded from '{detail.config.name}'"
    status.last_sync_at = datetime.utcnow()
    status.last_sync_status = "success"
    status.last_sync_message = message
    status.consecutive_failures = 0
    db.commit()

    logger.info(message)
    result = {"status": "success", "message": message, "lot_count": len(entries)}
    await _broadcast_status(status, result, extra_type="sale_updated")
    return result


async def refresh_sale_order_options(db) -> dict:
    """Re-query FairEntry for the Fair's available Sale Orders and replace
    the cached dropdown options. Auto-selects the sole option when there's
    exactly one and nothing is selected yet, but never triggers a sync."""
    connection = get_or_create_fairentry_connection(db)
    status = get_or_create_fairentry_sync_status(db, "sale")

    try:
        client = await _authenticate(connection)
    except _NotConfigured as e:
        return {"status": "skipped", "message": str(e), "options": []}
    except FairEntryError as e:
        return {"status": "error", "message": str(e), "options": []}

    try:
        sale_orders = await asyncio.to_thread(client.get_sale_orders, True)
    except FairEntryError as e:
        return {"status": "error", "message": str(e), "options": []}

    db.query(FairEntrySaleOrderOption).delete()
    for sale_order in sale_orders:
        db.add(FairEntrySaleOrderOption(
            id=sale_order.id, name=sale_order.name, entry_count=sale_order.entry_count
        ))

    # Drop cached lots for any Sale Order that no longer exists upstream -
    # otherwise a deleted/archived FairEntry sale would linger here forever.
    fresh_ids = {sale_order.id for sale_order in sale_orders}
    stale_lot_ids = [
        row.id for row in db.query(SaleProgram.id)
        .filter(SaleProgram.sale_order_id.isnot(None), ~SaleProgram.sale_order_id.in_(fresh_ids)).all()
    ]
    if stale_lot_ids:
        db.query(BidderLot).filter(BidderLot.lot_id.in_(stale_lot_ids)).delete(synchronize_session=False)
        db.query(SaleProgram).filter(SaleProgram.id.in_(stale_lot_ids)).delete(synchronize_session=False)

    if status.selected_sale_order_id is not None and status.selected_sale_order_id not in fresh_ids:
        status.selected_sale_order_id = None
        status.selected_sale_order_name = None

    if len(sale_orders) == 1 and not status.selected_sale_order_id:
        status.selected_sale_order_id = sale_orders[0].id
        status.selected_sale_order_name = sale_orders[0].name

    db.commit()

    await broadcast_message({"type": "sale_orders_updated"})
    await broadcast_message({"type": "fairentry_sale_sync_status", **status_to_dict(status)})
    if stale_lot_ids:
        await broadcast_message({"type": "sale_updated"})

    options = [{"id": so.id, "name": so.name, "entry_count": so.entry_count} for so in sale_orders]
    return {"status": "success", "message": f"Found {len(options)} sale order(s)", "options": options}


def select_sale_order(db, sale_order_id: int) -> dict:
    """Switch which Sale Order is active. Rows for every previously-synced
    Sale Order stay cached (tagged by sale_order_id), so this just changes
    which tag is "active" - no re-sync needed, the switch is instant. Only
    triggers a fetch on the next explicit Sync Now / auto-sync tick if this
    particular Sale Order has never been synced before (its cache is empty)."""
    status = get_or_create_fairentry_sync_status(db, "sale")
    changed = status.selected_sale_order_id != sale_order_id

    option = db.query(FairEntrySaleOrderOption).filter(FairEntrySaleOrderOption.id == sale_order_id).first()
    status.selected_sale_order_id = sale_order_id
    status.selected_sale_order_name = option.name if option else None

    if changed:
        # A different Sale Order's lots have no relationship to the previous
        # position - resetting avoids pointing at a lot that means nothing here.
        session = get_or_create_session(db)
        session.current_lot_index = -1

    db.commit()
    return status_to_dict(status)


async def _maybe_run_due_sync(db, target: str, perform_fn):
    status = get_or_create_fairentry_sync_status(db, target)
    if not status.sync_enabled:
        return

    interval = timedelta(minutes=status.sync_interval_minutes or 15)
    if status.last_sync_at and datetime.utcnow() - status.last_sync_at < interval:
        return

    await perform_fn(db)


async def fairentry_sync_loop():
    """Background task: periodically checks whether either sync target
    (buyers or sale) is due for an auto-sync."""
    while True:
        await asyncio.sleep(SYNC_CHECK_TICK_SECONDS)
        db = SessionLocal()
        try:
            await _maybe_run_due_sync(db, "buyers", perform_buyer_sync)
            await _maybe_run_due_sync(db, "sale", perform_sale_sync)
        except Exception:
            logger.exception("Unexpected error in FairEntry sync loop")
        finally:
            db.close()
