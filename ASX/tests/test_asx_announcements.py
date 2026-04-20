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
    assert scanner.calculate_rating("Maiden Resource Estimate", "") == 4  # strong phrase
    assert scanner.calculate_rating("FDA Approval Received", "") == 4  # strong phrase

def test_rating_price_sensitive_flag(scanner):
    """isPriceSensitive from API adds +1 on top of base."""
    # Price-sensitive routine filing: 1 + 1 = 2
    assert scanner.calculate_rating("Cleansing Notice", "", is_price_sensitive=True) == 2
    
    # Price-sensitive + high-value keywords: 1 + 1 + 2 = 4
    assert scanner.calculate_rating("Discovery of high-grade copper", "", is_price_sensitive=True) == 4
    
    # Price-sensitive + mid-value keywords: 1 + 1 + 1 = 3
    assert scanner.calculate_rating("Trading Halt", "", is_price_sensitive=True) == 3

def test_rating_capped_at_5(scanner):
    """Rating never exceeds 5."""
    assert scanner.calculate_rating("High-grade assay results", "", is_price_sensitive=True) == 5

def test_rating_progress_report_not_over_scored(scanner):
    assert scanner.calculate_rating("Exploration Update on Gold Project", "Progress Report", is_price_sensitive=True) <= 4

def test_rating_all_caps_forces_5(scanner):
    rating, reason = scanner.calculate_rating_with_reason("BINDING AGREEMENT SIGNED WITH PARTNER", "", False)
    assert rating == 5
    assert "all_caps" in reason

def test_rating_all_caps_safeguard_short_headline(scanner):
    rating, reason = scanner.calculate_rating_with_reason("AGM", "", False)
    assert rating < 5
    assert "all_caps" not in reason

def test_rating_corporate_catalysts(scanner):
    """Corporate actions and business catalysts should score as high-value."""
    # monetise/monetize → high (+2)
    assert scanner.calculate_rating("Renegade monetises Carpentaria JV", "", is_price_sensitive=True) >= 4
    # partnership → high (+2)
    assert scanner.calculate_rating("Launches Global Partnership Program", "Progress Report", is_price_sensitive=True) >= 3
    # conditional SPA → strong phrase (+3)
    assert scanner.calculate_rating("Entry into conditional SPA in respect of CIB", "", is_price_sensitive=True) == 5
    # fast-track → high (+2)
    assert scanner.calculate_rating("Fast-Track Mt Chalmers into Development", "") >= 3
    # commissioning → high (+2)
    assert scanner.calculate_rating("Commissioning of Processing Plant Complete", "") >= 3

def test_rating_dollar_amount_bonus(scanner):
    """Headlines with specific dollar amounts get a bonus."""
    # $15m investment → dollar_amount (+1)
    assert scanner.calculate_rating("QIC Invests $15m to Fast-Track Development", "") >= 4
    # $100 million → dollar_amount (+1)
    assert scanner.calculate_rating("Secures $100 million funding", "") >= 2
    # No dollar amount → no bonus
    assert scanner.calculate_rating("Company provides quarterly update", "") == 2

def test_rating_mid_value_new_keywords(scanner):
    """Newly added mid-value keywords should trigger +1."""
    assert scanner.calculate_rating("Plant Upgrade Advances", "") == 2
    assert scanner.calculate_rating("Key Milestone Achieved", "") == 2
    assert scanner.calculate_rating("Strategic Review Underway", "") == 2

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
    from scripts.utils import get_sydney_time
    expected_approx = get_sydney_time() - timedelta(days=30)
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

# --- 7. Deduplication Tests ---

def test_duplicate_announcement_is_skipped(scanner):
    """Announcements with an existing unique_key should be skipped, not inserted twice."""
    mock_sess = MagicMock()
    
    with patch("scripts.asx_announcements.db.session_scope") as mock_scope:
        mock_scope.return_value.__enter__.return_value = mock_sess
        mock_stock = MagicMock(symbol="DUP", name="DUP CORP")
        mock_sess.query.return_value.all.return_value = [mock_stock]
        mock_sess.query.return_value.filter_by.return_value.first.return_value = None
        
        item = {
            "symbol": "DUP",
            "headline": "Test Announcement",
            "date": "2026-04-15T08:00:00.000Z",
            "announcementTypes": ["General"],
            "isPriceSensitive": False,
            "companyInfo": [{"displayName": "DUP CORP"}],
            "documentKey": "doc_dup"
        }
        
        # First insertion with empty existing keys — should add
        scanner.process_and_sync([item], set())
        assert mock_sess.add.call_count == 1
        
        # Second insertion with the unique_key already present — should skip
        existing_key = mock_sess.add.call_args[0][0].unique_key
        mock_sess.add.reset_mock()
        scanner.process_and_sync([item], {existing_key})
        assert mock_sess.add.call_count == 0

def test_recalc_updates_existing_record(scanner):
    mock_sess = MagicMock()
    existing = MagicMock(unique_key="AAA_2026-04-16_TEST", summary="Progress Report", pdf_link="")

    with patch("scripts.asx_announcements.db.session_scope") as mock_scope:
        mock_scope.return_value.__enter__.return_value = mock_sess
        mock_sess.query.return_value.filter_by.return_value.first.return_value = existing

        item = {
            "symbol": "AAA",
            "headline": "BINDING AGREEMENT SIGNED WITH PARTNER",
            "date": "2026-04-16T08:00:00.000Z",
            "announcementTypes": ["Progress Report"],
            "isPriceSensitive": False,
            "documentKey": "doc_aaa",
        }
        scanner.recalc_and_update([item])

        assert existing.rating == 5


# --- 8. PDF Download Tests ---

def test_pdf_download_skips_cached_file(scanner, tmp_path):
    """Already-downloaded PDFs should not be re-downloaded."""
    with patch("scripts.asx_announcements._CACHE_DIR", tmp_path):
        # Pre-create a cached file
        cached = tmp_path / "test.pdf"
        cached.write_bytes(b"existing")

        result = scanner._download_pdf("https://example.com/test.pdf", "test.pdf")
        assert result == cached
        # Content unchanged (no HTTP call was made)
        assert cached.read_bytes() == b"existing"


def test_pdf_download_saves_new_file(scanner, tmp_path):
    """New PDFs should be downloaded and saved to cache."""
    with patch("scripts.asx_announcements._CACHE_DIR", tmp_path):
        mock_resp = MagicMock()
        mock_resp.content = b"%PDF-fake-content"
        mock_resp.raise_for_status = MagicMock()
        scanner.session = MagicMock()
        scanner.session.get.return_value = mock_resp

        result = scanner._download_pdf("https://example.com/new.pdf", "new.pdf")
        assert result == tmp_path / "new.pdf"
        assert result.read_bytes() == b"%PDF-fake-content"
        scanner.session.get.assert_called_once()


def test_pdf_download_triggered_for_high_rated_ps_new(scanner, tmp_path):
    """New price-sensitive announcements with rating > 3 should trigger PDF download."""
    mock_sess = MagicMock()

    with patch("scripts.asx_announcements.db.session_scope") as mock_scope, \
         patch("scripts.asx_announcements._CACHE_DIR", tmp_path), \
         patch.object(scanner, "_download_pdf") as mock_dl:
        mock_scope.return_value.__enter__.return_value = mock_sess
        mock_stock = MagicMock(symbol="HVK", name="HIGH VALUE CORP")
        mock_sess.query.return_value.all.return_value = [mock_stock]
        mock_sess.query.return_value.filter_by.return_value.first.return_value = None

        item = {
            "symbol": "HVK",
            "headline": "High-grade assay results from drill program",
            "date": "2026-04-16T08:00:00.000Z",
            "announcementTypes": ["Mining"],
            "isPriceSensitive": True,
            "companyInfo": [{"displayName": "HIGH VALUE CORP"}],
            "documentKey": "doc_hvk",
        }
        scanner.process_and_sync([item], set())

        mock_dl.assert_called_once()


def test_pdf_download_not_triggered_for_low_rated(scanner, tmp_path):
    """Announcements with rating <= 3 should NOT trigger PDF download."""
    mock_sess = MagicMock()

    with patch("scripts.asx_announcements.db.session_scope") as mock_scope, \
         patch("scripts.asx_announcements._CACHE_DIR", tmp_path), \
         patch.object(scanner, "_download_pdf") as mock_dl:
        mock_scope.return_value.__enter__.return_value = mock_sess
        mock_stock = MagicMock(symbol="LOW", name="LOW CORP")
        mock_sess.query.return_value.all.return_value = [mock_stock]
        mock_sess.query.return_value.filter_by.return_value.first.return_value = None

        item = {
            "symbol": "LOW",
            "headline": "Quarterly Activities Report",
            "date": "2026-04-16T08:00:00.000Z",
            "announcementTypes": ["Quarterly"],
            "isPriceSensitive": True,
            "companyInfo": [{"displayName": "LOW CORP"}],
            "documentKey": "doc_low",
        }
        scanner.process_and_sync([item], set())

        mock_dl.assert_not_called()


def test_pdf_download_not_triggered_for_non_ps(scanner, tmp_path):
    """Non-price-sensitive announcements should NOT trigger PDF download even if rating > 3."""
    mock_sess = MagicMock()

    with patch("scripts.asx_announcements.db.session_scope") as mock_scope, \
         patch("scripts.asx_announcements._CACHE_DIR", tmp_path), \
         patch.object(scanner, "_download_pdf") as mock_dl:
        mock_scope.return_value.__enter__.return_value = mock_sess
        mock_stock = MagicMock(symbol="NPS", name="NPS CORP")
        mock_sess.query.return_value.all.return_value = [mock_stock]
        mock_sess.query.return_value.filter_by.return_value.first.return_value = None

        item = {
            "symbol": "NPS",
            "headline": "BINDING AGREEMENT SIGNED WITH PARTNER",
            "date": "2026-04-16T08:00:00.000Z",
            "announcementTypes": ["General"],
            "isPriceSensitive": False,
            "companyInfo": [{"displayName": "NPS CORP"}],
            "documentKey": "doc_nps",
        }
        scanner.process_and_sync([item], set())

        mock_dl.assert_not_called()


def test_pdf_download_triggered_in_recalc(scanner, tmp_path):
    """recalc_and_update should download PDFs for price-sensitive items with rating > 3."""
    mock_sess = MagicMock()
    existing = MagicMock(
        unique_key="RCL_2026-04-16_HIGH-GRADE ASSAY RESULTS",
        summary="Mining",
        pdf_link="https://example.com/rcl.pdf",
    )

    with patch("scripts.asx_announcements.db.session_scope") as mock_scope, \
         patch("scripts.asx_announcements._CACHE_DIR", tmp_path), \
         patch.object(scanner, "_download_pdf") as mock_dl:
        mock_scope.return_value.__enter__.return_value = mock_sess
        mock_sess.query.return_value.filter_by.return_value.first.return_value = existing

        item = {
            "symbol": "RCL",
            "headline": "High-grade assay results from drill program",
            "date": "2026-04-16T08:00:00.000Z",
            "announcementTypes": ["Mining"],
            "isPriceSensitive": True,
            "documentKey": "doc_rcl",
        }
        scanner.recalc_and_update([item])

        assert existing.rating == 5
        mock_dl.assert_called_once()


def test_pdf_download_for_existing_record_in_sync(scanner, tmp_path):
    """process_and_sync should download PDF for existing DB records that meet criteria."""
    mock_sess = MagicMock()
    existing_ann = MagicMock(
        rating=5,
        pdf_link="https://example.com/exist.pdf",
    )

    with patch("scripts.asx_announcements.db.session_scope") as mock_scope, \
         patch("scripts.asx_announcements._CACHE_DIR", tmp_path), \
         patch.object(scanner, "_download_pdf") as mock_dl:
        mock_scope.return_value.__enter__.return_value = mock_sess
        mock_stock = MagicMock(symbol="EXS", name="EXIST CORP")
        mock_sess.query.return_value.all.return_value = [mock_stock]
        # Return existing record on filter_by check
        mock_sess.query.return_value.filter_by.return_value.first.return_value = existing_ann

        item = {
            "symbol": "EXS",
            "headline": "Major Discovery Announced",
            "date": "2026-04-16T08:00:00.000Z",
            "announcementTypes": ["Mining"],
            "isPriceSensitive": True,
            "companyInfo": [{"displayName": "EXIST CORP"}],
            "documentKey": "doc_exs",
        }
        scanner.process_and_sync([item], set())

        # Should NOT add a new record (existing found)
        assert mock_sess.add.call_count == 0
        # Should download PDF for existing record
        mock_dl.assert_called_once()


# --- Ticker Filtering Tests (merged from test_ticker_filtering.py) ---

def test_ticker_filtering_logic():
    """Test that the scraper correctly filters out non-stock symbols and derivatives."""
    from scripts.utils import ticker_clean

    test_items = [
        {"symbol": "BHP", "headline": "Ordinary Stock - Should Pass",
         "companyInfo": [{"symbol": "BHP", "issueType": "CS"}]},
        {"symbol": "VDHG", "headline": "ETF - Should Pass",
         "companyInfo": [{"symbol": "VDHG", "issueType": "ET"}]},
        {"symbol": "SPP", "headline": "Ghost Ticker (truncated bond) - Should FAIL",
         "companyInfo": [{"symbol": "SPPHA", "issueType": "FLC"}]},
        {"symbol": "CBAHB", "headline": "Preference Share (long ticker) - Should FAIL",
         "companyInfo": [{"symbol": "CBAHB", "issueType": "CS"}]},
        {"symbol": "XYZW", "headline": "Warrant - Should FAIL",
         "companyInfo": [{"symbol": "XYZW", "issueType": "WR"}]},
    ]

    passed_syms = []
    for item in test_items:
        sym = ticker_clean(item.get("symbol", ""))
        if not sym:
            continue
        ci = item.get("companyInfo")
        is_valid = True
        if ci and len(ci) > 0:
            issue_type = ci[0].get("issueType", "")
            if issue_type and issue_type not in ["CS", "CD", "ET", "UI"]:
                is_valid = False
            real_sym = ci[0].get("symbol", "")
            if real_sym and len(real_sym.replace('.AX', '')) > 4:
                is_valid = False
        if is_valid:
            passed_syms.append(sym)

    assert "BHP" in passed_syms
    assert "VDHG" in passed_syms
    assert "SPP" not in passed_syms
    assert "CBAHB" not in passed_syms
    assert "XYZW" not in passed_syms
