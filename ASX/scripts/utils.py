import os
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# --- ANSI Colors for Logging ---
class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"

class ColoredFormatter(logging.Formatter):
    """Custom logging formatter with colors."""
    FORMATS = {
        logging.DEBUG: f"{Colors.DIM}%(message)s{Colors.RESET}",
        logging.INFO: f"{Colors.GREEN}%(message)s{Colors.RESET}",
        logging.WARNING: f"{Colors.YELLOW}{Colors.BOLD}WARNING: %(message)s{Colors.RESET}",
        logging.ERROR: f"{Colors.RED}{Colors.BOLD}ERROR: %(message)s{Colors.RESET}",
        logging.CRITICAL: f"{Colors.RED}{Colors.BOLD}CRITICAL: %(message)s{Colors.RESET}",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def get_logger(name: str = "asx_pipeline") -> logging.Logger:
    """Get a configured logger with colors."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setFormatter(ColoredFormatter())
        logger.addHandler(ch)
    return logger

logger = get_logger()

# --- Config Management ---
def get_root_dir() -> Path:
    """Returns the project root directory."""
    return Path(__file__).parent.parent

def load_config() -> Dict[str, Any]:
    """Load settings from config/settings.yaml."""
    root_dir = get_root_dir()
    settings_path = root_dir / "config" / "settings.yaml"
    
    cfg = {}
    if settings_path.exists():
        with open(settings_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    
    api = cfg.get("api", {})
    scanners = cfg.get("scanners", {})
    
    return {
        "API_BASE": api.get("announcements_base", "https://asx.api.markitdigital.com/asx-research/1.0/markets/announcements"),
        "HEADER_API": api.get("company_header", "https://asx.api.markitdigital.com/asx-research/1.0/companies/{}/header"),
        "PDF_CDN": api.get("pdf_cdn", "https://cdn-api.markitdigital.com/apiman-gateway/ASX/asx-research/1.0/file/"),
        "PDF_TOKEN": api.get("pdf_token", "83ff96335c2d45a094df02a206a39ff4"),
        "ITEMS_PER_PAGE": scanners.get("items_per_page", 100),
        "ANN_JSON_OUT": root_dir / "output" / "asx_announcements.json",
        "PLC_JSON_OUT": root_dir / "output" / "asx_placements.json",
        "CAT_JSON_OUT": root_dir / "output" / "asx_catalysts.json",
        "ANA_JSON_OUT": root_dir / "output" / "asx_analyzer.json",
    }

# --- Shared Helpers ---
def normalize_date(date_str: str) -> str:
    """Normalize various date formats to YYYY-MM-DD."""
    if not date_str:
        return ""
    try:
        # Pydantic date objects or ISO strings
        if isinstance(date_str, datetime):
            return date_str.strftime("%Y-%m-%d")
        if "/" in date_str:
            return datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
        return date_str[:10]
    except Exception:
        return date_str

def clean_company_name(name: str) -> str:
    """Standard cleaning for company names."""
    if not name:
        return ""
    return name.replace("LIMITED", "LTD").replace("INCORPORATED", "INC").strip().upper()

def ticker_to_ax(symbol: str) -> str:
    """Ensure symbol has .AX suffix."""
    sym = symbol.strip().upper()
    return f"{sym}.AX" if not sym.endswith(".AX") else sym

def ticker_clean(symbol: str) -> str:
    """Remove .AX suffix."""
    return symbol.replace(".AX", "").replace(".ax", "").strip().upper()

def generate_sparkline(prices_str: str, width: int = 100, height: int = 30) -> str:
    """Generate an SVG sparkline from a comma-separated string of prices."""
    if not prices_str or len(prices_str.split(',')) < 2:
        return "-"
    
    try:
        prices = [float(p) for p in prices_str.split(',')]
        if not prices: return "-"
        
        # Normalize prices to fit SVG height
        min_p, max_p = min(prices), max(prices)
        if max_p == min_p:
            # Flat line
            return f'<svg width="{width}" height="{height}"><line x1="0" y1="{height/2}" x2="{width}" y2="{height/2}" stroke="#94a3b8" stroke-width="2"/></svg>'
        
        range_p = max_p - min_p
        
        # Calculate points
        points = []
        n = len(prices)
        for i, p in enumerate(prices):
            x = (i / (n - 1)) * width
            # Invert y because SVG y goes down
            y = height - ((p - min_p) / range_p) * height
            points.append(f"{x:.1f},{y:.1f}")
        
        color = "#10b981" if prices[-1] >= prices[0] else "#ef4444" # Green if up, Red if down
        
        path_data = "M " + " L ".join(points)
        return (
            f'<svg width="{width}" height="{height}" style="overflow:visible">'
            f'<path d="{path_data}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
            f'</svg>'
        )
    except Exception:
        return "-"
