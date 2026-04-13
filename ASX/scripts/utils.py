"""
ASX Pipeline Utilities

Centralized logging, configuration loading, and shared helper functions.
"""

import os
import re
import yaml
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, Optional

# --- Constants ---
DEFAULT_TIMEOUT = 30
DEFAULT_MCAP_FILTER = 15_000_000 # $15M AUD

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
    """Get a configured logger with colors and thread-safe handling."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setFormatter(ColoredFormatter())
        logger.addHandler(ch)
    return logger

# Global logger instance
logger = get_logger()

# --- Config Management ---
def get_root_dir() -> Path:
    """Returns the project root directory."""
    return Path(__file__).parent.parent

def load_config() -> Dict[str, Any]:
    """Load settings from config/settings.yaml with fallback error handling."""
    root_dir = get_root_dir()
    settings_path = root_dir / "config" / "settings.yaml"
    
    cfg = {}
    if settings_path.exists():
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load settings from {settings_path}: {e}")
    else:
        logger.warning(f"Settings file not found at {settings_path}. Using defaults.")
    
    return cfg

# --- Shared Helpers ---
def normalize_date(d: Any) -> str:
    """Standardize date strings/objects to YYYY-MM-DD."""
    if not d: return datetime.now().strftime("%Y-%m-%d")
    if isinstance(d, (datetime, date)): 
        return d.strftime("%Y-%m-%d")
    # Handle common ASX API date strings "2024-04-10T..."
    if isinstance(d, str):
        return d.split("T")[0]
    return str(d)

def ticker_clean(s: str) -> str:
    """Normalize Tickers to 3-byte uppercase string without .AX."""
    if not s: return ""
    return s.upper().replace(".AX", "").strip()

def clean_filename(s: str) -> str:
    """Clean string for use as a safe filename."""
    if not s: return "announcement"
    # Standardize separators and remove illegal chars
    s = s.replace(' / ', ' ').replace(' - ', ' ')
    s = re.sub(r'[^\w\s\-\[\]]', '', s) 
    s = " ".join(s.split())
    s = s.replace(' ', '_')
    return s[:100]

def get_pdf_filename(ev: Dict) -> str:
    """Generate the standardized ASX PDF filename: YYYY-MM-DD_[TICKER]_HEADLINE.pdf"""
    date_val = normalize_date(ev.get("date"))
    symbol = ticker_clean(ev.get("symbol") or "ASX")
    headline = clean_filename(ev.get("headline", "announcement"))
    return f"{date_val}_[{symbol}]_{headline}.pdf"

def generate_sparkline(prices_str: Optional[str]) -> str:
    """Generate a compact SVG sparkline from a comma-separated string of prices."""
    if not prices_str: return ""
    try:
        pts = [float(p) for p in prices_str.split(",") if p.strip()]
        if len(pts) < 2: return ""
        
        # Normalize
        min_p, max_p = min(pts), max(pts)
        diff = max_p - min_p if max_p != min_p else 1
        
        # SVG parameters
        w, h = 100, 30
        norm_pts = [(i * (w / (len(pts)-1)), h - ((p - min_p) / diff * h)) for i, p in enumerate(pts)]
        path_data = "L".join([f"{x:.1f},{y:.1f}" for x, y in norm_pts])
        
        # Trend Color
        is_up = pts[-1] >= pts[0]
        color = "#00C853" if is_up else "#FF5252"
        
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none">' \
              f'<path d="M{path_data}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>' \
              f'</svg>'
        
        import base64
        return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"
    except Exception:
        return ""
