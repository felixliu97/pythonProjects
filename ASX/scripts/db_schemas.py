from pydantic import BaseModel, Field, validator, HttpUrl
from typing import List, Optional, Dict, Union
from datetime import date, datetime

class StockSchema(BaseModel):
    symbol: str = Field(..., description="ASX Ticker without .AX")
    name: str
    industry: Optional[str] = None
    stock_type: str = Field(..., pattern="^(growth|foundation|etf)$")

    @validator('symbol')
    def clean_symbol(cls, v):
        return v.upper().replace(".AX", "").strip()

class MilestoneSchema(BaseModel):
    """Note: These keys match the original YAML keys for compatibility"""
    Time: str = Field(..., alias="time_label")
    Event: str = Field(..., alias="event_desc")
    
    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

class CatalystSchema(BaseModel):
    """
    Interface model that maps relational children to lists for LLM/Dashboard compatibility.
    """
    Ticker: str
    Company: str
    Sector: Optional[str] = None
    Catalysts: List[str] = []
    Risks: List[str] = []
    Earnings_Window: List[str] = []
    CR_Risk: str
    Probability: str
    Core_Notes: str
    Timeline: List[Dict[str, str]] = [] # [{"Time": "...", "Event": "..."}]

    @validator('Ticker')
    def clean_ticker(cls, v):
        return v.upper().replace(".AX", "").strip()

class MarketTrendSchema(BaseModel):
    symbol: str
    current_price: Optional[float] = None
    market_cap: Optional[int] = None
    pe: Optional[float] = None
    ps: Optional[float] = None
    yield_val: Optional[float] = None
    score: float = 0.0
    price_change_1d: float = 0.0
    price_diff_1d: float = 0.0
    price_change_5d: float = 0.0
    price_diff_5d: float = 0.0
    momentum: float = 0.0
    volatility: float = 0.0
    volume_change: float = 0.0
    rsi: float = 50.0
    price_history: Optional[str] = None
    market_date: Optional[date] = None
    
    @validator('symbol')
    def clean_symbol(cls, v):
        return v.upper().replace(".AX", "").strip()

class AnnouncementSchema(BaseModel):
    ASX_Code: str
    Company: str
    Headline: str
    Date: date
    Summary: Optional[str] = ""
    PDF_Link: Optional[str] = ""
    Rating: int = Field(2, ge=1, le=5)

    @validator('ASX_Code')
    def clean_asx_code(cls, v):
        return v.upper().replace(".AX", "").strip()

class PlacementSchema(BaseModel):
    ASX_Code: str
    Company: str
    Headline: str
    Date: date
    CR_Price: Optional[float] = None
    Current_Price: Optional[float] = None
    Price_Diff_Percent: Optional[float] = Field(None, alias="Price_Diff_%")
    PDF_Link: Optional[str] = ""

    class Config:
        populate_by_name = True

    @validator('ASX_Code')
    def clean_asx_code(cls, v):
        return v.upper().replace(".AX", "").strip()
