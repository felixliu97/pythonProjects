"""
ASX Database Models (Total Decoupling & Maximum Compatibility)

NOTE: Using traditional Column definitions to avoid any Mapper ambiguity
caused by the absence of physical foreign keys. Each table is 100% independent.
"""

from datetime import datetime, date
from sqlalchemy import (
    Column, String, Integer, Float, Date, DateTime, 
    Text, BigInteger, Boolean, text
)
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class Stock(Base):
    __tablename__ = 'stocks'
    __table_args__ = {'schema': 'asx'}
    
    symbol = Column(String(20), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    industry = Column(String(255))
    stock_type = Column(String(50), nullable=False)

    def __repr__(self) -> str:
        return f"<Stock(symbol='{self.symbol}', name='{self.name}')>"

class MarketTrend(Base):
    __tablename__ = 'market_trends'
    __table_args__ = {'schema': 'asx'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), index=True) # Flat storage
    
    current_price = Column(Float)
    market_cap = Column(BigInteger)
    pe = Column(Float)
    yield_val = Column(Float)
    score = Column(Float, default=0.0)
    price_change_1d = Column(Float, default=0.0)
    price_diff_1d = Column(Float, default=0.0)
    price_change_5d = Column(Float, default=0.0)
    price_history = Column(Text)
    price_diff_5d = Column(Float, default=0.0)
    momentum = Column(Float, default=0.0)
    volatility = Column(Float, default=0.0)
    volume_change = Column(Float, default=0.0)
    rsi = Column(Float, default=50.0)
    
    market_date = Column(Date, index=True)
    valid_from = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), index=True)
    valid_to = Column(DateTime, index=True)
    is_active = Column(Boolean, default=True, index=True)

class CatalystMaster(Base):
    __tablename__ = 'catalyst_masters'
    __table_args__ = {'schema': 'asx'}
    
    symbol = Column(String(20), primary_key=True)
    company = Column(String(255), nullable=False)
    sector = Column(String(255))
    cr_risk = Column(String(500))
    cr_risk_reason = Column(Text)
    breakout_probability = Column(String(500))
    breakout_probability_reason = Column(Text)
    core_notes = Column(Text)
    rating = Column(String(50), default="观望")

class CatalystItem(Base):
    __tablename__ = 'catalyst_items'
    __table_args__ = {'schema': 'asx'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), index=True)
    item_type = Column(String(50), index=True)
    content = Column(Text, nullable=False)
    label = Column(String(200)) 
    
    valid_from = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), index=True)
    valid_to = Column(DateTime, index=True)
    is_active = Column(Boolean, default=True, index=True)

class Announcement(Base):
    __tablename__ = 'announcements'
    __table_args__ = {'schema': 'asx'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), index=True)
    company = Column(String(255))
    headline = Column(String(1000))
    event_date = Column(Date, index=True)
    summary = Column(Text)
    pdf_link = Column(String(1000))
    rating = Column(Integer, default=2)
    unique_key = Column(String(500), unique=True, index=True)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

class Placement(Base):
    __tablename__ = 'placements'
    __table_args__ = {'schema': 'asx'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), index=True)
    company = Column(String(255))
    headline = Column(String(1000))
    event_date = Column(Date, index=True)
    cr_price = Column(Float)
    current_price = Column(Float)
    price_diff_percent = Column(Float)
    pdf_link = Column(String(1000))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
