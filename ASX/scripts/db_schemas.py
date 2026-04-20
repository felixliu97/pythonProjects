from pydantic import BaseModel, Field, field_validator, HttpUrl, ConfigDict, model_validator
from typing import List, Optional, Dict, Union
from datetime import date, datetime


CATALYST_STAGE_VALUES = {
    "阶段1-无人关注期",
    "阶段2-验证突破期",
    "阶段3-现金流确认期",
    "阶段4-行业统治期",
    "阶段5-估值溢价期",
    "未分类",
}

CATALYST_RATING_VALUES = {"强力买入", "买入", "观望", "卖出", "强力卖出"}
CATALYST_CR_RISK_VALUES = {"极低", "低", "中低", "中", "中高", "高"}
CATALYST_BREAKOUT_VALUES = {"低", "中低", "中", "中高", "高", "极高"}

CATALYST_CR_RISK_SCORES = {"极低": 0, "低": 1, "中低": 2, "中": 3, "中高": 4, "高": 5}
CATALYST_BREAKOUT_SCORES = {"低": 0, "中低": 1, "中": 2, "中高": 3, "高": 4, "极高": 5}


def _require_non_empty_text(value: Optional[str], field_name: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be a non-empty string")
    return text


def validate_catalyst_records(raw_records) -> List["CatalystSchema"]:
    if raw_records is None:
        return []
    if isinstance(raw_records, dict):
        raw_records = [raw_records]
    if not isinstance(raw_records, list):
        raise ValueError("Catalyst YAML top-level structure must be a list")
    return [CatalystSchema(**item) for item in raw_records]


def derive_catalyst_rating(cr_risk: Optional[str], breakout_probability: Optional[str]) -> str:
    cr = (cr_risk or "").strip()
    bp = (breakout_probability or "").strip()

    if cr not in CATALYST_CR_RISK_SCORES or bp not in CATALYST_BREAKOUT_SCORES:
        return "观望"

    score_delta = CATALYST_BREAKOUT_SCORES[bp] - CATALYST_CR_RISK_SCORES[cr]

    if score_delta >= 4:
        return "强力买入"
    if score_delta >= 2:
        return "买入"
    if score_delta >= -1:
        return "观望"
    if score_delta >= -3:
        return "卖出"
    return "强力卖出"

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

    Date: str = Field(..., alias="time_label")
    Event: str = Field(..., alias="event_desc")

    @field_validator('Date')
    @classmethod
    def validate_date(cls, v: str) -> str:
        text = _require_non_empty_text(v, "Timeline.Date")
        try:
            datetime.strptime(text, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("Timeline.Date must use exact YYYY-MM-DD format") from exc
        return text

    @field_validator('Event')
    @classmethod
    def validate_event(cls, v: str) -> str:
        return _require_non_empty_text(v, "Timeline.Event")

class CatalystSchema(BaseModel):
    """
    Interface model that maps relational children to lists for LLM/Dashboard compatibility.
    """
    Ticker: str
    Stage: Optional[str] = "未分类"
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
    Timeline: List[Dict[str, str]] = [] # [{"Date": "...", "Event": "..."}]

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='before')
    @classmethod
    def apply_default_rating(cls, data):
        if not isinstance(data, dict):
            return data

        rating = str(data.get("Rating") or "").strip()
        if rating:
            return data

        normalized = dict(data)
        normalized["Rating"] = derive_catalyst_rating(
            normalized.get("CR_Risk"),
            normalized.get("Breakout_Probability") or normalized.get("Probability"),
        )
        return normalized

    @field_validator('Ticker')
    @classmethod
    def clean_ticker(cls, v: str) -> str:
        return _require_non_empty_text(v, "Ticker").upper().replace(".AX", "").strip()

    @field_validator('Stage')
    @classmethod
    def validate_stage(cls, v: Optional[str]) -> str:
        value = (v or "未分类").strip()
        if value not in CATALYST_STAGE_VALUES:
            raise ValueError(f"Stage must be one of: {sorted(CATALYST_STAGE_VALUES)}")
        return value

    @field_validator('Company')
    @classmethod
    def validate_company(cls, v: str) -> str:
        return _require_non_empty_text(v, "Company")

    @field_validator('Sector')
    @classmethod
    def validate_sector(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _require_non_empty_text(v, "Sector")

    @field_validator('CR_Risk')
    @classmethod
    def validate_cr_risk(cls, v: str) -> str:
        value = _require_non_empty_text(v, "CR_Risk")
        if value not in CATALYST_CR_RISK_VALUES:
            raise ValueError(f"CR_Risk must be one of: {sorted(CATALYST_CR_RISK_VALUES)}")
        return value

    @field_validator('Breakout_Probability')
    @classmethod
    def validate_breakout_probability(cls, v: Optional[str]) -> str:
        value = _require_non_empty_text(v, "Breakout_Probability")
        if value not in CATALYST_BREAKOUT_VALUES:
            raise ValueError(f"Breakout_Probability must be one of: {sorted(CATALYST_BREAKOUT_VALUES)}")
        return value

    @field_validator('Core_Notes')
    @classmethod
    def validate_core_notes(cls, v: str) -> str:
        return _require_non_empty_text(v, "Core_Notes")

    @field_validator('Rating')
    @classmethod
    def validate_rating(cls, v: str) -> str:
        value = (v or "观望").strip()
        if value not in CATALYST_RATING_VALUES:
            raise ValueError(f"Rating must be one of: {sorted(CATALYST_RATING_VALUES)}")
        return value

    @field_validator('CR_Risk_Reason', 'Breakout_Probability_Reason', mode='before')
    @classmethod
    def normalize_optional_reason(cls, v):
        if v is None:
            return ""
        return str(v).strip()

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

    @field_validator('Catalysts', 'Risks')
    @classmethod
    def validate_string_lists(cls, v: List[str], info) -> List[str]:
        cleaned = []
        for idx, item in enumerate(v):
            text = str(item).strip()
            if not text:
                raise ValueError(f"{info.field_name}[{idx}] must be a non-empty string")
            cleaned.append(text)
        return cleaned

    @field_validator('Timeline', mode='before')
    @classmethod
    def validate_timeline(cls, v):
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("Timeline must be a list of {Date, Event} objects")
        return [MilestoneSchema(**item).model_dump(by_alias=False) for item in v]

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
    volume: Optional[int] = 0
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
