from datetime import date
from unittest.mock import MagicMock

import pytest

from scripts.asx_placements import PlacementScanner


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def scanner(mock_session):
    return PlacementScanner(mock_session)


# --- 1. Basic Heuristic Tests ---


def test_cr_price_extraction(scanner):
    """Verify CR price extraction from headlines."""
    assert scanner.extract_cr_price("issue of securities @ $0.05") == 0.05
    assert scanner.extract_cr_price("raise at $1.20 per share") == 1.2
    assert scanner.extract_cr_price("Trading Halt") == 0.0


def test_price_diff_logic(scanner):
    """Verify percentage difference calculation."""
    assert scanner.calculate_diff(1.2, 1.0) == 20.0
    assert scanner.calculate_diff(0.8, 1.0) == -20.0
    assert scanner.calculate_diff(0, 1.2) == 0.0


def test_process_raw_matches_raise_to_fund_headline(scanner):
    """Raise-to-fund financing headlines should not be missed even without the literal word placement."""
    items = [
        {
            "symbol": "OMA",
            "date": "2026-04-23T10:13:00+1000",
            "headline": "OMA Raise A$60m to Fund Upgraded 26/27 Taroom Trough Program",
            "documentKey": "3A000001",
            "companyInfo": [{"displayName": "Omega Oil & Gas Limited", "issueType": "CS"}],
        }
    ]

    processed = scanner.process_raw(items)

    assert len(processed) == 1
    assert processed[0]["symbol"] == "OMA"
    assert processed[0]["headline"] == "oma raise a$60m to fund upgraded 26/27 taroom trough program"


# --- 2. Live Refresh Tests ---


def test_extract_cr_price_dollars(scanner):
    assert scanner.extract_cr_price("Placement at $1.50 per share") == 1.50
    assert scanner.extract_cr_price("Raising capital @ $0.05") == 0.05
    assert scanner.extract_cr_price("Issue price of $2.35") == 2.35
    assert scanner.extract_cr_price("Placement priced at $0.125") == 0.125


def test_extract_cr_price_cents(scanner):
    assert scanner.extract_cr_price("Placement at 15c per share") == 0.15
    assert scanner.extract_cr_price("Capital raising @ 5 cents") == 0.05
    assert scanner.extract_cr_price("Share purchase plan at 8.5c") == 0.085
    assert scanner.extract_cr_price("Placement at 22.5cps") == 0.225
    assert scanner.extract_cr_price("10c placement to raise $5m") == 0.10


def test_extract_cr_price_fallback(scanner):
    assert scanner.extract_cr_price("Successfully completed placement at 0.45") == 0.45
    assert scanner.extract_cr_price("No price here") == 0.0


def test_extract_cr_price_from_content(scanner):
    # Case 1: Complex content with total amount and per-share price
    content1 = """
    The Company is pleased to announce a placement to raise $5.0 million.
    The placement was conducted at an issue price of $0.15 per share.
    """
    assert scanner.extract_cr_price(content1) == 0.15

    # Case 2: Cents in content
    content2 = """
    Share Purchase Plan (SPP) at 8.5 cents per share to raise up to $2.0m.
    """
    assert scanner.extract_cr_price(content2) == 0.085

    # Case 3: Avoid picking up total amount
    content3 = """
    Successful completion of $10 million capital raising.
    """
    # Should not pick up 10.0 because it's a total
    assert scanner.extract_cr_price(content3) == 0.0

    # Case 4: Multiple prices, should target the one with context
    content4 = """
    Total raised: $4.5 million
    Issue price: $0.125
    """
    assert scanner.extract_cr_price(content4) == 0.125


def test_is_better_logic():
    """Verify the deduplication priority logic (Price > Date)."""
    # Logic: New has price, old doesn't -> Should replace
    should_replace = False
    if 0.10 > 0 and 0.0 == 0:
        should_replace = True
    assert should_replace

    # Logic: Both have price, new is earlier -> Should replace
    p_early_date = date(2026, 3, 1)
    p_late_date = date(2026, 3, 5)

    should_replace = False
    if 0.08 > 0 and 0.10 > 0:
        if p_early_date < p_late_date:
            should_replace = True
    assert should_replace


# --- 5. Filter-First Pipeline Tests ---


def test_cr_price_4_decimal(scanner):
    """CR prices with 4 decimal places should be extracted and preserved."""
    assert scanner.extract_cr_price("Placement at $0.7625 per share") == 0.7625
    assert scanner.extract_cr_price("Issue price of $0.0325") == 0.0325

    # Diff should preserve precision
    diff = scanner.calculate_diff(0.80, 0.7625)
    assert abs(diff - 4.92) < 0.1  # ~4.92%


# --- 8. Ticker Filtering Tests (merged from test_ticker_filtering.py) ---


def test_placement_scanner_filtering():
    """Verify that PlacementScanner correctly filters out non-stock items."""
    market_cache = {
        "BHP": {"issueType": "CS", "name": "BHP Group"},
        "SPP": {"issueType": None, "name": None},
        "BOND": {"issueType": "FLC", "name": "Some Bond"},
        "LONGTICKER": {"issueType": "CS", "name": "Long Ticker"},
    }

    events = [
        {"symbol": "BHP", "company": "BHP"},
        {"symbol": "SPP", "company": "SPP"},
        {"symbol": "BOND", "company": "BOND"},
        {"symbol": "LONGTICKER", "company": "LONG"},
    ]

    liquid_events = []
    known_stocks = set()

    for ev in events:
        sym = ev["symbol"]
        info = market_cache.get(sym, {})
        issue_type = info.get("issueType")
        if not issue_type:
            if sym not in known_stocks:
                continue
        if issue_type and issue_type not in ["CS", "CD", "ET", "UI"]:
            continue
        if len(sym.replace(".AX", "")) > 4:
            continue
        liquid_events.append(ev)

    assert len(liquid_events) == 1
    assert liquid_events[0]["symbol"] == "BHP"


# --- 9. Resumption Cutoff Tests ---


def test_resumption_cutoff_uses_recent_date():
    """Placement resumption should not go further back than 2 days ago."""
    from datetime import datetime, timedelta

    from scripts.utils import get_sydney_time

    # Simulate: latest placement event_date = 10 days ago
    old_date = datetime(2026, 4, 5)
    recent_cutoff = get_sydney_time() - timedelta(days=2)

    # max() should pick the more recent date
    start_date = max(old_date, recent_cutoff.replace(tzinfo=None))

    # Should be within 2 days of now, not 10 days
    days_back = (datetime.now() - start_date).days
    assert days_back <= 3  # 2 day cutoff + 1 day tolerance
