import yaml
import os
import re
import json
from datetime import datetime

# Current reference date for "past" vs "future"
TODAY = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

class _C:
    R=chr(27)+'[0m'; GREEN=chr(27)+'[92m'; YELLOW=chr(27)+'[93m'
def _ok(m):   print(f"{_C.GREEN}{m}{_C.R}")
def _warn(m): print(f"{_C.YELLOW}{m}{_C.R}")

# Paths
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(os.path.dirname(ROOT_DIR), "config", "asx_catalysts.yaml")
JSON_OUT = os.path.join(os.path.dirname(ROOT_DIR), "output", "asx_catalysts.json")

def process_catalysts():
    """Headless data processing for Catalyst Radar"""
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            stocks = yaml.safe_load(f)
    except Exception as e:
        _warn(f"Error loading YAML from {JSON_FILE}: {e}")
        return

    def breakout_key(s):
        # Probability (High -> Low)
        p = s.get("Probability", "").strip()
        p_score = 0
        if p.startswith("极高"): p_score = -6
        elif p.startswith("高"): p_score = -5
        elif p.startswith("中高"): p_score = -4
        elif p.startswith("中低"): p_score = -2
        elif p.startswith("中"): p_score = -3
        elif p.startswith("低"): p_score = -1
        
        # CR Risk (Low -> High)
        cr = s.get("CR_Risk", "").strip()
        cr_score = 4 # Default to Medium
        if cr.startswith("极低"): cr_score = 1
        elif cr.startswith("低"): cr_score = 2
        elif cr.startswith("中低"): cr_score = 3
        elif cr.startswith("中"): cr_score = 4
        elif cr.startswith("高"): cr_score = 5
        elif cr.startswith("极高"): cr_score = 6
        
        return (p_score, cr_score, s.get("Ticker", ""))
        
    if stocks:
        stocks.sort(key=breakout_key)

    # Export processed data to JSON for the dashboard
    with open(JSON_OUT, 'w', encoding='utf-8') as f:
        json.dump({
            'catalysts': stocks, 
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }, f, indent=2, ensure_ascii=False)
        
    _ok(f"Headless Sync: Exported {len(stocks or [])} sorted stocks to {JSON_OUT}")

if __name__ == "__main__":
    process_catalysts()
