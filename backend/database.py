import logging
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

logger = logging.getLogger("adbackend")

# Keep in sync with the THEMES keys in frontend/src/themes.js
ALLOWED_THEMES = {"classic", "fourh_green", "fourh_green_solid", "high_contrast"}
DEFAULT_THEME = "classic"

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/auction.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SaleProgram(Base):
    __tablename__ = "sale_programs"

    id = Column(Integer, primary_key=True, index=True)
    lot_number = Column(String, index=True)
    student_name = Column(String)
    department = Column(String)
    # Explicit display/lot order, independent of insertion order - set from
    # the uploaded sheet's row order, or from FairEntry's SaleNumber order.
    sort_order = Column(Integer, index=True, default=0)
    # FairEntry's SaleOrderEntry Id. NULL for manually-uploaded rows; present
    # for rows created by a Sale Order sync, so a re-sync can tell which
    # local rows it owns.
    fairentry_entry_id = Column(Integer, index=True, nullable=True)
    # FairEntry's SaleOrder Id this row belongs to. NULL for rows created
    # while no Sale Order is selected (pure manual upload). Multiple Sale
    # Orders' rows can coexist - only the one matching the "sale" sync
    # status's selected_sale_order_id is the active/displayed set, so
    # switching the dropdown selection is instant and doesn't require a
    # re-sync of the sale being switched to.
    sale_order_id = Column(Integer, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    bidders = relationship("BidderLot", back_populates="lot")

class Buyer(Base):
    __tablename__ = "buyers"
    
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(Integer, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    bids = relationship("BidderLot", back_populates="buyer")

class AuctionSession(Base):
    __tablename__ = "auction_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    current_lot_index = Column(Integer, default=-1)
    theme = Column(String, default=DEFAULT_THEME)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class FairEntryConnection(Base):
    """Shared FairEntry login, used by every sync target."""
    __tablename__ = "fairentry_connection"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    password_encrypted = Column(String)
    fair_title = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FairEntrySyncStatus(Base):
    """One row per sync target ('buyers' or 'sale'), each with its own
    enable/interval/status - the two feeds are unrelated and may run on
    different schedules. selected_sale_order_id/name are only meaningful
    for target='sale'."""
    __tablename__ = "fairentry_sync_status"

    id = Column(Integer, primary_key=True, index=True)
    target = Column(String, unique=True, index=True)
    sync_enabled = Column(Boolean, default=False)
    sync_interval_minutes = Column(Integer, default=15)
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String, default="never")
    last_sync_message = Column(Text, nullable=True)
    consecutive_failures = Column(Integer, default=0)
    selected_sale_order_id = Column(Integer, nullable=True)
    selected_sale_order_name = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FairEntrySaleOrderOption(Base):
    """Cache of the Fair's available Sale Orders, for the Sale List dropdown.
    Fully replaced every time the list is refreshed against FairEntry."""
    __tablename__ = "fairentry_sale_order_options"

    id = Column(Integer, primary_key=True)  # FairEntry's own SaleOrder Id
    name = Column(String)
    entry_count = Column(Integer)
    fetched_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_admin = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class BidderLot(Base):
    __tablename__ = "bidders_per_lot"
    
    id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(Integer, ForeignKey("sale_programs.id"))
    buyer_id = Column(Integer, ForeignKey("buyers.id"))
    lot_index = Column(Integer)  # Position in the sale program
    created_at = Column(DateTime, default=datetime.utcnow)
    
    lot = relationship("SaleProgram", back_populates="bidders")
    buyer = relationship("Buyer", back_populates="bids")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database tables"""
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _ensure_theme_column()
    _ensure_sale_program_columns()
    _ensure_default_admin()
    logger.info("Database initialized")

def _ensure_default_admin():
    """Seed a real `admin` row on a fresh database so the account is a normal
    DB-managed user from the start — visible in /api/users and changeable via
    the usual change-password flow, instead of a hardcoded bypass that never
    shows up there. Only runs when the users table is empty, so it never
    overwrites an existing account."""
    from auth import get_password_hash

    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            db.add(User(username="admin", password_hash=get_password_hash("admin123"), is_admin=True))
            db.commit()
            logger.info("No users found — created default admin user (admin/admin123). Change this password after logging in.")
    finally:
        db.close()

def _ensure_theme_column():
    """create_all() only creates missing tables, not missing columns on
    existing ones, so add `theme` by hand for databases created before it existed."""
    with engine.connect() as conn:
        columns = [row[1] for row in conn.execute(text("PRAGMA table_info(auction_sessions)"))]
        if "theme" not in columns:
            conn.execute(text(f"ALTER TABLE auction_sessions ADD COLUMN theme VARCHAR DEFAULT '{DEFAULT_THEME}'"))
            conn.commit()

def _ensure_sale_program_columns():
    """create_all() only creates missing tables, not missing columns on
    existing ones, so add sort_order/fairentry_entry_id/sale_order_id by hand
    for databases created before they existed."""
    with engine.connect() as conn:
        columns = [row[1] for row in conn.execute(text("PRAGMA table_info(sale_programs)"))]
        if "sort_order" not in columns:
            conn.execute(text("ALTER TABLE sale_programs ADD COLUMN sort_order INTEGER DEFAULT 0"))
        if "fairentry_entry_id" not in columns:
            conn.execute(text("ALTER TABLE sale_programs ADD COLUMN fairentry_entry_id INTEGER"))
        if "sale_order_id" not in columns:
            conn.execute(text("ALTER TABLE sale_programs ADD COLUMN sale_order_id INTEGER"))
        conn.commit()

def get_active_sale_order_id(db):
    """The Sale Order Id currently selected for the Sale List (target='sale'),
    or None if nothing is selected (pure manual-upload mode)."""
    status = db.query(FairEntrySyncStatus).filter(FairEntrySyncStatus.target == "sale").first()
    return status.selected_sale_order_id if status else None

def ordered_lots(db):
    """SaleProgram rows for the currently active Sale Order, in explicit lot
    order rather than relying on insertion/rowid order. Rows tagged with a
    different sale_order_id (a previously-synced, currently unselected Sale
    Order) are left alone but excluded from this view."""
    active_sale_order_id = get_active_sale_order_id(db)
    return (
        db.query(SaleProgram)
        .filter(SaleProgram.sale_order_id == active_sale_order_id)
        .order_by(SaleProgram.sort_order, SaleProgram.id)
    )

def get_or_create_session(db):
    """Get or create the current auction session"""
    session = db.query(AuctionSession).filter(AuctionSession.is_active == True).first()
    if not session:
        session = AuctionSession()
        db.add(session)
        db.commit()
        db.refresh(session)
    return session

def clamp_current_lot_index(session, lot_count: int):
    """Keep current_lot_index in range after a lot-count change (manual Sale
    Program upload or a FairEntry sale sync). Caller is expected to commit."""
    if session.current_lot_index >= lot_count:
        session.current_lot_index = lot_count - 1

def get_or_create_fairentry_connection(db):
    """Get or create the singleton FairEntry connection (credentials) row"""
    connection = db.query(FairEntryConnection).first()
    if not connection:
        connection = FairEntryConnection()
        db.add(connection)
        db.commit()
        db.refresh(connection)
    return connection

def get_or_create_fairentry_sync_status(db, target: str):
    """Get or create the sync status row for a given target ('buyers' or 'sale')"""
    status = db.query(FairEntrySyncStatus).filter(FairEntrySyncStatus.target == target).first()
    if not status:
        status = FairEntrySyncStatus(target=target)
        db.add(status)
        db.commit()
        db.refresh(status)
    return status
