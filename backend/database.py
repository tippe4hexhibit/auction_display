import logging
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

logger = logging.getLogger("adbackend")

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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

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
    logger.info("Database initialized")

def get_or_create_session(db):
    """Get or create the current auction session"""
    session = db.query(AuctionSession).filter(AuctionSession.is_active == True).first()
    if not session:
        session = AuctionSession()
        db.add(session)
        db.commit()
        db.refresh(session)
    return session
