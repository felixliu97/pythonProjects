"""
ASX Database Models

Defines the SQLAlchemy ORM models for the ASX Research Pipeline.
Includes temporal tracking (SCD Type 2) for technical and fundamental data.
Using 'symbol' as the primary/foreign key for all relationships.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, 
    Text, ForeignKey, BigInteger, Boolean
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Stock(Base):
    """
    Core metadata for an ASX Stock or ETF.
    """
    __tablename__ = 'stocks'
    __table_args__ = {'schema': 'asx'}
    
    symbol = Column(String(20), primary_key=True, index=True)
    name = Column(String(255))
    industry = Column(String(255))
    stock_type = Column(String(50)) 
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    market_trends = relationship("MarketTrend", back_populates="stock", cascade="all, delete-orphan")
    catalyst_master = relationship("CatalystMaster", back_populates="stock", uselist=False, cascade="all, delete-orphan")
    announcements = relationship("Announcement", back_populates="stock")
    placements = relationship("Placement", back_populates="stock")

    def __repr__(self):
        return f"<Stock(symbol='{self.symbol}', name='{self.name}')>"

class MarketTrend(Base):
    """
    Stores snapshots of technical and momentum metrics.
    Implements SCD Type 2 for temporal tracking.
    """
    __tablename__ = 'market_trends'
    __table_args__ = {'schema': 'asx'}
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), ForeignKey('asx.stocks.symbol', ondelete="CASCADE"), index=True)
    
    current_price = Column(Float)
    market_cap = Column(BigInteger)
    pe = Column(Float)
    ps = Column(Float)
    yield_val = Column(Float) 
    score = Column(Float)
    price_change_1d = Column(Float)
    price_diff_1d = Column(Float)
    price_change_5d = Column(Float)
    price_history = Column(Text)
    price_diff_5d = Column(Float)
    momentum = Column(Float)
    volatility = Column(Float)
    volume_change = Column(Float)
    rsi = Column(Float)
    
    # Authoritative session identifier (yfinance session date)
    market_date = Column(Date, index=True)
    
    # Temporal tracking
    valid_from = Column(DateTime, default=datetime.now, index=True)
    valid_to = Column(DateTime, nullable=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    stock = relationship("Stock", back_populates="market_trends")

class CatalystMaster(Base):
    """
    Anchor table for fundamental research data.
    """
    __tablename__ = 'catalyst_masters'
    __table_args__ = {'schema': 'asx'}
    
    symbol = Column(String(20), ForeignKey('asx.stocks.symbol', ondelete="CASCADE"), primary_key=True)
    
    company = Column(String(255))
    sector = Column(String(255))
    cr_risk = Column(String(500))
    probability = Column(String(500))
    core_notes = Column(Text)
    
    # Relationships
    stock = relationship("Stock", back_populates="catalyst_master")
    items = relationship("CatalystItem", back_populates="master", cascade="all, delete-orphan")

class CatalystItem(Base):
    """
    Unified storage for catalysts, risks, earnings windows, and milestones.
    Each item is tagged with an item_type discriminator.
    """
    __tablename__ = 'catalyst_items'
    __table_args__ = {'schema': 'asx'}
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), ForeignKey('asx.catalyst_masters.symbol', ondelete="CASCADE"), index=True)
    
    item_type = Column(String(50), index=True) # 'catalyst', 'risk', 'earnings', 'milestone'
    content = Column(Text, nullable=False)
    label = Column(String(200)) 
    
    # Temporal tracking
    valid_from = Column(DateTime, default=datetime.now, index=True)
    valid_to = Column(DateTime, nullable=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    master = relationship("CatalystMaster", back_populates="items")

class Announcement(Base):
    """
    Scraped corporate announcements and their summaries.
    """
    __tablename__ = 'announcements'
    __table_args__ = {'schema': 'asx'}
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), ForeignKey('asx.stocks.symbol', ondelete="CASCADE"), nullable=True, index=True)
    
    company = Column(String(255))
    headline = Column(String(1000))
    event_date = Column(Date, index=True)
    summary = Column(Text)
    pdf_link = Column(String(1000))
    rating = Column(Integer, default=2)
    unique_key = Column(String(500), unique=True, index=True)
    
    created_at = Column(DateTime, default=datetime.now)
    
    stock = relationship("Stock", back_populates="announcements")

class Placement(Base):
    """
    Scraped capital raising events and financial parameters.
    """
    __tablename__ = 'placements'
    __table_args__ = {'schema': 'asx'}
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), ForeignKey('asx.stocks.symbol', ondelete="CASCADE"), nullable=True, index=True)
    
    company = Column(String(255))
    headline = Column(String(1000))
    event_date = Column(Date, index=True)
    cr_price = Column(Float)
    current_price = Column(Float)
    price_diff_percent = Column(Float)
    pdf_link = Column(String(1000))
    
    created_at = Column(DateTime, default=datetime.now)
    
    stock = relationship("Stock", back_populates="placements")
