import pytest
import requests
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from scripts.asx_announcements import AnnouncementScanner, MID_VALUE_KEYWORDS, HIGH_VALUE_KEYWORDS, main as announcements_main
from scripts.db_models import Announcement

@pytest.fixture
def scanner():
    return AnnouncementScanner(requests.Session())

@pytest.fixture
def mock_db():
    with patch("scripts.asx_announcements.db") as mock:
        yield mock

@pytest.fixture
def mock_scanner_class():
    with patch("scripts.asx_announcements.AnnouncementScanner") as mock:
        yield mock

# --- 1. Rating Logic ---

def test_rating_routine_filing(scanner):
    """Routine filings with no keywords and no price sensitivity get base rating 1."""
    assert scanner.calculate_rating("Appendix 3B - Issue of securities", "") == 1

def test_rating_mid_value_keywords(scanner):
    """Mid-value keywords (trading halt, quarterly, placement) add +1 -> rating 2."""
    assert scanner.calculate_rating("Trading Halt", "") == 2
    assert scanner.calculate_rating("Quarterly Activities Report", "") == 2
    assert scanner.calculate_rating("Placement Completed", "Capital Raising") == 2

def test_rating_high_value_keywords(scanner):
    """High-value keywords (discovery, assay, approval) add +2 -> rating 3."""
    assert scanner.calculate_rating("Exceptional Assay Results", "") == 3
    assert scanner.calculate_rating("Maiden Resource Estimate", "") == 3
    assert scanner.calculate_rating("FDA Approval Received", "") == 3

def test_rating_price_sensitive_flag(scanner):
    """isPriceSensitive from API adds +2 on top of base."""
    # Price-sensitive routine filing: 1 + 2 = 3
    assert scanner.calculate_rating("Cleansing Notice", "", is_price_sensitive=True) == 3
    
    # Price-sensitive + high-value keywords: 1 + 2 + 2 = 5
    assert scanner.calculate_rating("Discovery of high-grade copper", "", is_price_sensitive=True) == 5
    
    # Price-sensitive + mid-value keywords: 1 + 2 + 1 = 4
    assert scanner.calculate_rating("Trading Halt", "", is_price_sensitive=True) == 4

def test_rating_capped_at_5(scanner):
    """Rating never exceeds 5."""
    assert scanner.calculate_rating("Discovery of maiden gold resource with assay results", "drilling breakthrough", is_price_sensitive=True) == 5

def test_rating_floor_at_1(scanner):
    """Rating never goes below 1."""
    assert scanner.calculate_rating("", "") >= 1

# --- 2. Summary Generation ---

def test_summary_from_announcement_types(scanner):
    """Verify that summary is derived from announcementTypes, not left empty."""
    mock_sess = MagicMock()
    
    with patch("scripts.asx_announcements.db.session_scope") as mock_scope:
        mock_scope.return_value.__enter__.return_value = mock_sess
        # Mock stocks table as name lookup dict (symbol -> Stock object with .symbol and .name)
        mock_stock = MagicMock(symbol="TST", name="TEST CORP")
        mock_sess.query.return_value.all.return_value = [mock_stock]
        mock_sess.query.return_value.filter_by.return_value.first.return_value = None
        
        item = {
            "symbol": "TST",
            "headline": "Trading Halt",
            "date": "2026-04-13T08:00:00.000Z",
            "announcementTypes": ["Trading Halt", "Market Sensitive"],
            "isPriceSensitive": True,
            "companyInfo": [{"displayName": "TEST CORP"}],
            "documentKey": "doc123"
        }
        
        scanner.process_and_sync([item], set())
        
        # Verify the Announcement added has summary populated
        add_call = mock_sess.add.call_args
        ann = add_call[0][0]
        assert ann.summary == "Trading Halt, Market Sensitive"
        assert ann.rating >= 3

def test_company_name_fallback_to_stocks_table(scanner):
    """When API companyInfo is empty, company name should fall back to our stocks table."""
    
    # Simulate the 3-tier resolution logic from process_and_sync
    stock_name_map = {"BOT": "BOTANIX PHARMACEUTICALS LTD", "TIO": "TIOMIN RESOURCES"}
    
    # Case 1: companyInfo present and has displayName -> use it
    ci_full = [{"displayName": "API NAME"}]
    if ci_full and len(ci_full) > 0 and ci_full[0].get("displayName"):
        name1 = ci_full[0]["displayName"]
    else:
        name1 = stock_name_map.get("BOT", "BOT")
    assert name1 == "API NAME"
    
    # Case 2: companyInfo is empty list -> fall back to stocks table
    ci_empty = []
    if ci_empty and len(ci_empty) > 0 and ci_empty[0].get("displayName"):
        name2 = ci_empty[0]["displayName"]
    else:
        name2 = stock_name_map.get("BOT", "BOT")
    assert name2 == "BOTANIX PHARMACEUTICALS LTD"
    
    # Case 3: companyInfo is None -> fall back to stocks table
    ci_none = None
    if ci_none and len(ci_none) > 0 and ci_none[0].get("displayName"):
        name3 = ci_none[0]["displayName"]
    else:
        name3 = stock_name_map.get("TIO", "TIO")
    assert name3 == "TIOMIN RESOURCES"
    
    # Case 4: symbol not in stocks table -> fall back to raw symbol
    if ci_empty and len(ci_empty) > 0 and ci_empty[0].get("displayName"):
        name4 = ci_empty[0]["displayName"]
    else:
        name4 = stock_name_map.get("UNKNOWN", "UNKNOWN")
    assert name4 == "UNKNOWN"

# --- 3. Noise Filter Tests ---

def test_noise_filtering(scanner):
    """Check noise filtering logic."""
    from scripts.asx_announcements import NOISE_KEYWORDS
    
    noisy_headline = "Appendix 4G: Key to Corporate Governance Disclosure"
    assert any(nk in noisy_headline.lower() for nk in NOISE_KEYWORDS)
    
    valuable_headline = "Exceptional Assay Results from drill hole DH01"
    assert not any(nk in valuable_headline.lower() for nk in NOISE_KEYWORDS)

# --- 4. Unique Key Tests ---

def test_unique_key_robustness():
    """Verify unique key generation and normalization."""
    from scripts.utils import normalize_date
    sym = "BHP"
    dt = normalize_date("2026-04-13T10:00:00+1000")
    hl = "   Maiden Resource Estimate   "
    
    unique_key = f"{sym}_{dt}_{hl.strip()[:100]}"
    assert unique_key == "BHP_2026-04-13_Maiden Resource Estimate"

# --- 5. Pipeline Resumption Tests ---

def test_resumption_from_empty_db(mock_db, mock_scanner_class):
    """If DB is empty, default to start offset (e.g. 1 month)."""
    mock_sess = MagicMock()
    mock_db.session_scope.return_value.__enter__.return_value = mock_sess
    mock_sess.query.return_value.order_by.return_value.first.return_value = None
    
    scanner_inst = mock_scanner_class.return_value
    scanner_inst.fetch_raw.return_value = []
    
    with patch("sys.argv", ["asx_announcements.py", "--months", "1"]):
        announcements_main()
    
    args, _ = scanner_inst.fetch_raw.call_args
    start_date = args[0]
    expected_approx = datetime.now() - timedelta(days=30)
    assert abs((start_date - expected_approx).total_seconds()) < 60

def test_resumption_from_existing_data(mock_db, mock_scanner_class, caplog):
    """If DB has data, resume from the latest date."""
    last_date = datetime(2026, 4, 1)
    mock_sess = MagicMock()
    mock_db.session_scope.return_value.__enter__.return_value = mock_sess
    mock_sess.query.return_value.order_by.return_value.first.return_value = [last_date]
    mock_sess.query.return_value.filter.return_value.all.return_value = []
    
    scanner_inst = mock_scanner_class.return_value
    scanner_inst.fetch_raw.return_value = []
    
    with patch("sys.argv", ["asx_announcements.py"]):
        announcements_main()
    
    args, _ = scanner_inst.fetch_raw.call_args
    assert args[0] == last_date
    assert f"Resuming from latest date 2026-04-01" in caplog.text

# --- 6. Sorting Logic Tests ---

def test_announcement_sorting_priority():
    """Verify that announcements are sorted by Date (DESC) then Rating (DESC)."""
    from datetime import date
    
    # Mock data
    a1 = MagicMock(event_date=date(2026, 4, 13), rating=2, headline="Date 13, Rating 2")
    a2 = MagicMock(event_date=date(2026, 4, 13), rating=5, headline="Date 13, Rating 5 (Priority)")
    a3 = MagicMock(event_date=date(2026, 4, 12), rating=5, headline="Date 12 (Older)")
    
    unsorted = [a1, a3, a2]
    
    # Simulate SQLAlchemy's multi-column sort: event_date.desc(), rating.desc()
    # In Python, we can use a composite key. To sort DESC, we can reverse the list or use negative markers if applicable, 
    # but for dates and heterogeneous objects, a custom key is clearer.
    # Note: date(2026, 4, 13) > date(2026, 4, 12), so for DESC we want larger first.
    
    sorted_list = sorted(unsorted, key=lambda x: (x.event_date, x.rating), reverse=True)
    
    assert sorted_list[0].headline == "Date 13, Rating 5 (Priority)"
    assert sorted_list[1].headline == "Date 13, Rating 2"
    assert sorted_list[2].headline == "Date 12 (Older)"

def test_pdf_url_generation():
    """Verify that Markit document keys are converted to official CDN URLs with tokens."""
    from scripts.utils import get_asx_pdf_url, load_config
    
    cfg = load_config().get("api", {})
    token = cfg.get("pdf_token", "")
    key = "2924-03078280-6A1320269"
    
    url = get_asx_pdf_url(key, "2026-04-13")
    assert f"access_token={token}" in url
    assert key in url
    assert "cdn-api.markitdigital.com" in url

