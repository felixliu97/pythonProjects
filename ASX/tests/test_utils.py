import pytest
from datetime import datetime
from scripts.utils import ticker_clean, normalize_date, generate_sparkline

# --- 1. Utility Tests ---

def test_ticker_clean():
    assert ticker_clean("BHP.AX") == "BHP"
    assert ticker_clean("  RIO  ") == "RIO"
    assert ticker_clean(None) == ""

def test_normalize_date():
    assert normalize_date("2026-04-13T10:00:00+1000") == "2026-04-13"
    expected = datetime.now().strftime("%Y-%m-%d")
    assert normalize_date("") == expected

def test_generate_sparkline():
    svg_data = generate_sparkline("1.0,1.1,1.2")
    assert svg_data.startswith("data:image/svg+xml;base64,")
