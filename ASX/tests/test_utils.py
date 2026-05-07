from datetime import datetime

from scripts.utils import generate_sparkline, get_sydney_time, normalize_date, ticker_clean

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


# --- 2. Timezone Tests ---


def test_normalize_date_utc_to_aest():
    """Verify that late-night UTC dates are correctly converted to the next day in AEST."""
    utc_str = "2026-04-14T22:30:00.000Z"
    normalized = normalize_date(utc_str)
    assert normalized == "2026-04-15"


def test_normalize_date_early_utc_to_aest():
    """Verify that early UTC dates stay on the same day in AEST if they haven't crossed midnight."""
    utc_str = "2026-04-14T02:30:00.000Z"
    normalized = normalize_date(utc_str)
    assert normalized == "2026-04-14"


def test_get_sydney_time():
    """Verify that get_sydney_time returns a localized datetime."""
    st = get_sydney_time()
    assert st.tzinfo is not None
    assert str(st.tzinfo) == "Australia/Sydney"


def test_normalize_date_naive():
    """Verify naive datetimes are handled as local market dates."""
    dt = datetime(2026, 4, 15, 10, 0, 0)
    assert normalize_date(dt) == "2026-04-15"


def test_normalize_date_empty():
    """Verify empty input returns current Sydney date."""
    normalized = normalize_date(None)
    assert len(normalized) == 10
    assert normalized.startswith("202")

# --- 3. Data Type Safety (Sort/Compare) ---

def test_mixed_type_sort_safety():
    """Verify that we can safely sort mixed date/string lists using str conversion."""
    import datetime
    items = [
        {"Date": datetime.date(2026, 5, 7)},
        {"Date": ""},
        {"Date": datetime.date(2026, 5, 5)}
    ]
    # This simulates the fix in run.py
    items.sort(key=lambda x: str(x.get("Date", "")), reverse=True)
    
    assert str(items[0]["Date"]) == "2026-05-07"
    assert str(items[1]["Date"]) == "2026-05-05"
    assert items[2]["Date"] == ""

def test_mixed_type_equality():
    """Verify that date objects and strings require explicit conversion for equality."""
    import datetime
    d = datetime.date(2026, 5, 7)
    s = "2026-05-07"
    assert d != s
    assert str(d) == s
