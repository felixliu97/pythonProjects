import pytest
import requests
from unittest.mock import MagicMock, patch
from datetime import date
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

# --- 2. Live Refresh Tests ---

def test_refresh_all_prices_logic(scanner):
    """Verify that refresh_all_prices updates DB records with API data."""
    p1 = Placement(symbol="ABC", cr_price=1.0, current_price=1.1, price_diff_percent=10.0)
    
    mock_sess_obj = MagicMock()
    mock_sess_obj.query.return_value.all.return_value = [p1]
    
    # Mock API: New Price 1.2
    scanner.fetch_market_info = MagicMock(return_value=(1.2, 1000000, "ABC Corp"))
    
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
    scanner.fetch_market_info = MagicMock(return_value=(0.002, 10000000, "RED MOUNTAIN MINING LIMITED"))
    
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
    
    scanner.fetch_market_info = MagicMock(return_value=(None, None, None))
    
    with patch("scripts.asx_placements.db.session_scope") as mock_scope:
        mock_scope.return_value.__enter__.return_value = mock_sess_obj
        scanner.refresh_all_prices()
        
        assert p1.current_price == 0.5 # Unchanged

# --- 3. Sync Logic Tests ---

def test_sync_to_db_uses_live_name_fallback(scanner):
    """Verify that new placements use live API name if announcement is missing it."""
    ev = {
        "symbol": "NEW",
        "date": "2026-04-10",
        "company": "", # Missing in news feed
        "headline": "Placement at $1.00",
        "pdf_link": "link"
    }
    
    scanner.fetch_market_info = MagicMock(return_value=(1.1, 100000000, "Official Name Corp"))
    
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
        assert added_placement.company == "Official Name Corp" # Backfilled from API
        assert added_placement.current_price == 1.1
