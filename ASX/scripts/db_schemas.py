from pydantic import BaseModel, Field, field_validator, HttpUrl, ConfigDict
from typing import List, Optional, Dict, Union
from datetime import date, datetime

class StockSchema(BaseModel):
    symbol: str = Field(..., description="ASX Ticker without .AX")
    name: str
    industry: Optional[str] = None
    stock_type: str = Field(..., pattern="^(growth|foundation|etf|announcement)$")

    @field_validator('symbol')
    @classmethod
    def clean_symbol(cls, v: str) -> str:
        return v.upper().replace(".AX", "").strip()

class MilestoneSchema(BaseModel):
    """Note: These keys match the original YAML keys for compatibility"""
    model_config = ConfigDict(populate_by_name=True)
    
    Time: str = Field(..., alias="time_label")
    Event: str = Field(..., alias="event_desc")

class CatalystSchema(BaseModel):
    """
    Interface model that maps relational children to lists for LLM/Dashboard compatibility.
    """
    Ticker: str
    Company: str
    Sector: Optional[str] = None
    Catalysts: List[str] = []
    Risks: List[str] = []
    CR_Risk: str
    CR_Risk_Reason: Optional[str] = ""
    Breakout_Probability: Optional[str] = Field(None, alias="Probability")
    Breakout_Probability_Reason: Optional[str] = ""
    Core_Notes: str
    Rating: str = "观望"
    Timeline: List[Dict[str, str]] = [] # [{"Time": "...", "Event": "..."}]

    model_config = ConfigDict(populate_by_name=True)

    @field_validator('Ticker')
    @classmethod
    def clean_ticker(cls, v: str) -> str:
        return v.upper().replace(".AX", "").strip()

    @field_validator('Catalysts', 'Risks', mode='before')
    @classmethod
    def handle_dict_items(cls, v):
        """Convert any dict-style list items (key: value) to plain strings."""
        if not isinstance(v, list):
            return v
        processed = []
        for item in v:
            if isinstance(item, dict):
                # Convert {key: value} to "key: value"
                processed.append(", ".join([f"{k}: {v}" for k, v in item.items()]))
            else:
                processed.append(str(item))
        return processed

class MarketTrendSchema(BaseModel):
    symbol: str
    current_price: Optional[float] = None
    market_cap: Optional[int] = None
    pe: Optional[float] = None
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
    
    @field_validator('symbol')
    @classmethod
    def clean_symbol(cls, v: str) -> str:
        return v.upper().replace(".AX", "").strip()

class AnnouncementSchema(BaseModel):
    ASX_Code: str
    Company: str
    Headline: str
    Date: date
    Summary: Optional[str] = ""
    PDF_Link: Optional[str] = ""
    Rating: int = Field(2, ge=1, le=5)

    @field_validator('ASX_Code')
    @classmethod
    def clean_asx_code(cls, v: str) -> str:
        return v.upper().replace(".AX", "").strip()

class PlacementSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ASX_Code: str
    Company: str
    Headline: str
    Date: date
    CR_Price: Optional[float] = None
    Current_Price: Optional[float] = None
    Price_Diff_Percent: Optional[float] = Field(None, alias="Price_Diff_%")
    PDF_Link: Optional[str] = ""

    @field_validator('ASX_Code')
    @classmethod
    def clean_asx_code(cls, v: str) -> str:
        return v.upper().replace(".AX", "").strip()
