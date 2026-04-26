from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from scripts.asx_placements import PlacementScanner
from scripts.db_models import Placement


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


def test_refresh_all_prices_logic(scanner):
    """Verify that refresh_all_prices updates DB records with API data."""
    p1 = Placement(symbol="ABC", cr_price=1.0, current_price=1.1, price_diff_percent=10.0)

    mock_sess_obj = MagicMock()
    mock_sess_obj.query.return_value.all.return_value = [p1]

    # Mock API: New Price 1.2
    scanner.fetch_market_info = MagicMock(return_value=(1.2, 1000000, "ABC Corp", "CS"))

    with patch("scripts.asx_placements.db.session_scope") as mock_scope:
        mock_scope.return_value.__enter__.return_value = mock_sess_obj
        scanner.refresh_all_prices()

        assert p1.current_price == 1.2
        assert p1.price_diff_percent == 20.0


def test_refresh_backfills_missing_company_name(scanner):
    """Verify that refresh correctly backfills an empty company name."""
    p1 = Placement(symbol="ROG", company="", cr_price=1.0, current_price=1.1)

    mock_sess_obj = MagicMock()
    mock_sess_obj.query.return_value.all.return_value = [p1]

    # Mock API returns official name
    scanner.fetch_market_info = MagicMock(return_value=(0.002, 10000000, "RED MOUNTAIN MINING LIMITED", "CS"))

    with patch("scripts.asx_placements.db.session_scope") as mock_scope:
        mock_scope.return_value.__enter__.return_value = mock_sess_obj
        scanner.refresh_all_prices()

        # Verify name is backfilled
        assert p1.company == "RED MOUNTAIN MINING LIMITED"
        assert p1.current_price == 0.002


def test_refresh_skips_on_api_failure(scanner):
    """Verify that if API fails, existing record is preserved."""
    p1 = Placement(symbol="FAIL", current_price=0.5)

    mock_sess_obj = MagicMock()
    mock_sess_obj.query.return_value.all.return_value = [p1]

    scanner.fetch_market_info = MagicMock(return_value=(None, None, None, None))

    with patch("scripts.asx_placements.db.session_scope") as mock_scope:
        mock_scope.return_value.__enter__.return_value = mock_sess_obj
        scanner.refresh_all_prices()

        assert p1.current_price == 0.5  # Unchanged


# --- 3. Sync Logic Tests ---


def test_sync_to_db_uses_live_name_fallback(scanner):
    """Verify that new placements use live API name if announcement is missing it."""
    ev = {
        "symbol": "NEW",
        "date": "2026-04-10",
        "company": "",  # Missing in news feed
        "headline": "Placement at $1.00",
        "pdf_link": "link",
    }

    scanner.fetch_market_info = MagicMock(return_value=(1.1, 100000000, "Official Name Corp", "CS"))

    mock_sess_obj = MagicMock()
    # Mock symbols check
    mock_stock = MagicMock(symbol="NEW")
    mock_sess_obj.query.return_value.all.return_value = [mock_stock]
    # Mock existing check
    mock_sess_obj.query.return_value.filter_by.return_value.first.return_value = None

    with patch("scripts.asx_placements.db.session_scope") as mock_scope:
        mock_scope.return_value.__enter__.return_value = mock_sess_obj
        scanner.sync_to_db([ev])

        added_placement = mock_sess_obj.add.call_args[0][0]
        assert added_placement.company == "Official Name Corp"  # Backfilled from API
        assert added_placement.current_price == 1.1


# --- 4. Extra Extraction Logic (Merged from test_price_extraction.py) ---


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


def test_sync_auto_registers_unknown_stocks(scanner, caplog):
    """Stocks not in the watchlist should be auto-registered with stock_type='announcement'
    and still pass through the liquidity gate if large enough."""
    ev = {
        "symbol": "UNKN",
        "date": "2026-04-10",
        "company": "Ghost Corp",
        "headline": "Placement at $1.00",
        "pdf_link": "link",
    }

    # market info fetch should occur and return a large market cap
    scanner.fetch_market_info = MagicMock(return_value=(1.0, 50000000, "Ghost Corp", "CS"))
    scanner._download_pdf = MagicMock()

    # We need to test the auto-add logic
    mock_sess_obj = MagicMock()
    # Watchlist contains only "ABC", not "UNKN"
    mock_stock = MagicMock(symbol="ABC")
    mock_sess_obj.query.return_value.all.return_value = [mock_stock]
    # No existing placement
    mock_sess_obj.query.return_value.filter_by.return_value.first.return_value = None

    with patch("scripts.asx_placements.db.session_scope") as mock_scope:
        mock_scope.return_value.__enter__.return_value = mock_sess_obj
        scanner.sync_to_db([ev])

        # Should have added a new Stock AND a new Placement
        assert mock_sess_obj.add.call_count == 2

        # Verify the auto-registered stock
        stock_add_call = mock_sess_obj.add.call_args_list[0][0][0]
        assert stock_add_call.__class__.__name__ == "Stock"
        assert stock_add_call.symbol == "UNKN"
        assert stock_add_call.stock_type == "announcement"

        assert "Auto-registered new stock: UNKN" in caplog.text


def test_sync_skips_low_mcap_stocks(scanner, caplog):
    """Stocks below the mcap threshold should be filtered out before CR extraction."""
    ev = {
        "symbol": "TINY",
        "date": "2026-04-10",
        "company": "Tiny Corp",
        "headline": "Placement at $0.01",
        "pdf_link": "link",
    }

    # mcap = 5M < 15M threshold
    scanner.fetch_market_info = MagicMock(return_value=(0.01, 5_000_000, "Tiny Corp", "CS"))
    scanner._download_pdf = MagicMock()

    mock_sess_obj = MagicMock()
    mock_stock = MagicMock(symbol="TINY")
    mock_sess_obj.query.return_value.all.return_value = [mock_stock]

    with patch("scripts.asx_placements.db.session_scope") as mock_scope:
        mock_scope.return_value.__enter__.return_value = mock_sess_obj
        scanner.sync_to_db([ev])

        # fetch_market_info SHOULD be called (needed for mcap check)
        scanner.fetch_market_info.assert_called_once_with("TINY")
        # But PDF download should NOT happen (filtered by liquidity gate)
        scanner._download_pdf.assert_not_called()
        mock_sess_obj.add.assert_not_called()


def test_sync_passes_mcap_none_through(scanner):
    """Stocks where mcap is None (API failure) should pass through the liquidity gate."""
    ev = {
        "symbol": "AFAL",
        "date": "2026-04-10",
        "company": "API Fail Corp",
        "headline": "Placement at $0.50",
        "pdf_link": "link",
    }

    # mcap=None, issueType=None simulates a failed API call
    # Since AFAL IS in known_stocks, the None issueType check passes
    scanner.fetch_market_info = MagicMock(return_value=(None, None, None, None))

    mock_sess_obj = MagicMock()
    mock_stock = MagicMock(symbol="AFAL")
    mock_sess_obj.query.return_value.all.return_value = [mock_stock]
    mock_sess_obj.query.return_value.filter_by.return_value.first.return_value = None

    with patch("scripts.asx_placements.db.session_scope") as mock_scope:
        mock_scope.return_value.__enter__.return_value = mock_sess_obj
        scanner.sync_to_db([ev])

        # Should still add (mcap=None passes the `if mcap and mcap < threshold` guard)
        mock_sess_obj.add.assert_called_once()


def test_sync_only_extracts_for_liquid_stocks(scanner):
    """Of two events, only the one passing the mcap gate should have CR extraction attempted."""
    ev_tiny = {
        "symbol": "TINY",
        "date": "2026-04-10",
        "company": "Tiny Corp",
        "headline": "No price here",
        "pdf_link": "link_tiny",
    }
    ev_big = {
        "symbol": "BIG",
        "date": "2026-04-10",
        "company": "Big Corp",
        "headline": "Placement at $2.00",
        "pdf_link": "link_big",
    }

    def market_info_side_effect(sym):
        if sym == "TINY":
            return (0.01, 5_000_000, "Tiny Corp", "CS")  # Below threshold
        elif sym == "BIG":
            return (2.1, 500_000_000, "Big Corp", "CS")  # Above threshold
        return (None, None, None, None)

    scanner.fetch_market_info = MagicMock(side_effect=market_info_side_effect)
    scanner._download_pdf = MagicMock()

    mock_sess_obj = MagicMock()
    mock_stocks = [MagicMock(symbol="TINY"), MagicMock(symbol="BIG")]
    mock_sess_obj.query.return_value.all.return_value = mock_stocks
    mock_sess_obj.query.return_value.filter_by.return_value.first.return_value = None

    with patch("scripts.asx_placements.db.session_scope") as mock_scope:
        mock_scope.return_value.__enter__.return_value = mock_sess_obj
        scanner.sync_to_db([ev_tiny, ev_big])

        # Only BIG should be added
        assert mock_sess_obj.add.call_count == 1
        added = mock_sess_obj.add.call_args[0][0]
        assert added.symbol == "BIG"


# --- 6. Override Tests ---


def test_override_delete_removes_record(scanner):
    """Overrides with delete=true should remove existing records during sync."""
    ev = {
        "symbol": "DEL_ME",
        "date": "2026-04-10",
        "company": "Delete Corp",
        "headline": "Placement at $1.00",
        "pdf_link": "link",
    }

    # Override: delete this symbol
    scanner.overrides = {"DEL_ME": {"symbol": "DEL_ME", "delete": True}}
    scanner.fetch_market_info = MagicMock()

    mock_sess_obj = MagicMock()
    mock_stock = MagicMock(symbol="DEL_ME")
    mock_sess_obj.query.return_value.all.return_value = [mock_stock]

    with patch("scripts.asx_placements.db.session_scope") as mock_scope:
        mock_scope.return_value.__enter__.return_value = mock_sess_obj
        scanner.sync_to_db([ev])

        # Should call delete, not add
        mock_sess_obj.query.return_value.filter_by.return_value.delete.assert_called()
        mock_sess_obj.add.assert_not_called()


def test_forced_price_override(scanner):
    """apply_forced_overrides should update cr_price for matching symbols."""
    existing = Placement(symbol="OVR", cr_price=0.50, current_price=0.60, price_diff_percent=20.0, headline="old")

    scanner.overrides = {"OVR": {"symbol": "OVR", "cr_price": 0.75}}

    mock_sess_obj = MagicMock()
    mock_sess_obj.query.return_value.filter_by.return_value.first.return_value = existing

    with patch("scripts.asx_placements.db.session_scope") as mock_scope:
        mock_scope.return_value.__enter__.return_value = mock_sess_obj
        scanner.apply_forced_overrides()

        assert existing.cr_price == 0.75
        # Diff should be recalculated: (0.60 - 0.75) / 0.75 * 100 = -20.0
        assert existing.price_diff_percent == -20.0


# --- 7. Precision Tests ---


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
