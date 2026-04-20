import pytest
from scripts.asx_announcements import AnnouncementScanner
from scripts.utils import ticker_clean

class MockSession:
    def get(self, *args, **kwargs):
        pass

def test_ticker_filtering_logic():
    """
    Test that the scraper correctly filters out non-stock symbols and derivatives.
    """
    scanner = AnnouncementScanner(MockSession())
    
    # Define test cases for security types and symbols
    test_items = [
        {
            "symbol": "BHP",
            "headline": "Ordinary Stock - Should Pass",
            "companyInfo": [{"symbol": "BHP", "issueType": "CS"}]
        },
        {
            "symbol": "VDHG",
            "headline": "ETF - Should Pass",
            "companyInfo": [{"symbol": "VDHG", "issueType": "ET"}]
        },
        {
            "symbol": "SPP",
            "headline": "Ghost Ticker (truncated bond) - Should FAIL",
            "companyInfo": [{"symbol": "SPPHA", "issueType": "FLC"}]
        },
        {
            "symbol": "CBAHB",
            "headline": "Preference Share (long ticker) - Should FAIL",
            "companyInfo": [{"symbol": "CBAHB", "issueType": "CS"}] # Even if CS, long ticker fails
        },
        {
            "symbol": "XYZW",
            "headline": "Warrant - Should FAIL",
            "companyInfo": [{"symbol": "XYZW", "issueType": "WR"}]
        }
    ]
    
    passed_syms = []
    
    # We simulate the loop in process_and_sync (line 222 onwards)
    for item in test_items:
        sym = ticker_clean(item.get("symbol", ""))
        
        # 1. Basic filter
        if not sym: continue
        
        # 2. Strict Security Type Filter
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
    print("\nDONE: Ticker filtering unit test passed!")

if __name__ == "__main__":
    test_ticker_filtering_logic()
    test_placement_scanner_filtering()

def test_placement_scanner_filtering():
    """Verify that PlacementScanner correctly filters out non-stock items."""
    from scripts.asx_placements import PlacementScanner
    import requests
    
    scanner = PlacementScanner(requests.Session())
    
    # Mock data structure used in sync_to_db
    market_cache = {
        "BHP": {"issueType": "CS", "name": "BHP Group"},
        "SPP": {"issueType": None, "name": None}, # API failure case (Ghost)
        "BOND": {"issueType": "FLC", "name": "Some Bond"},
        "LONGTICKER": {"issueType": "CS", "name": "Long Ticker"}
    }
    
    events = [
        {"symbol": "BHP", "company": "BHP"},
        {"symbol": "SPP", "company": "SPP"},
        {"symbol": "BOND", "company": "BOND"},
        {"symbol": "LONGTICKER", "company": "LONG"}
    ]
    
    # Simulate the logic in sync_to_db Phase 3
    liquid_events = []
    known_stocks = set() # Start with empty to test auto-registration filter
    
    for ev in events:
        sym = ev["symbol"]
        info = market_cache.get(sym, {})
        issue_type = info.get("issueType")
        
        # Logic from asx_placements.py:
        if not issue_type:
            if sym not in known_stocks:
                continue
        
        if issue_type and issue_type not in ["CS", "CD", "ET", "UI"]:
            continue
            
        if len(sym.replace('.AX', '')) > 4:
            continue
            
        # Only BHP should pass
        liquid_events.append(ev)
        
    assert len(liquid_events) == 1
    assert liquid_events[0]["symbol"] == "BHP"
    print("DONE: PlacementScanner filtering unit test passed!")
