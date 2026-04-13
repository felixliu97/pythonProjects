"""
ASX Placement Scanner (Best Practice Refactor)

Detailed extraction of capital raising events.
Implements Global Price Refresh with optimized bulk updates.
"""

import argparse
import time
import requests
import yaml
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional, Tuple, Set

try:
    from db_manager import db
    from db_models import Stock, Placement
    from db_schemas import PlacementSchema
    from utils import logger, load_config, normalize_date, get_root_dir, ticker_clean, DEFAULT_TIMEOUT, DEFAULT_MCAP_FILTER
except ImportError:
    from scripts.db_manager import db
    from scripts.db_models import Stock, Placement
    from scripts.db_schemas import PlacementSchema
    from scripts.utils import logger, load_config, normalize_date, get_root_dir, ticker_clean, DEFAULT_TIMEOUT, DEFAULT_MCAP_FILTER

# --- Configuration ---
_CFG = load_config()
_API = _CFG.get("api", {})
API_BASE = _API.get("announcements_base", "https://asx.api.markitdigital.com/asx-research/1.0/markets/announcements")
PRICE_API = _API.get("company_header", "https://asx.api.markitdigital.com/asx-research/1.0/companies/{}/header")
ITEMS_PER_PAGE = _CFG.get("ITEMS_PER_PAGE", 1000)

PLACEMENT_KEYWORDS = (
    "placement", "capital rais", "capital raise", "share purchase plan", "spp",
    "equity raising", "entitlement offer", "rights issue"
)

class PlacementScanner:
    """Encapsulates the capital raising extraction and sync logic."""
    
    def __init__(self, session: requests.Session):
        self.session = session
        self.overrides = self._load_overrides()

    def extract_cr_price(self, headline: str) -> float:
        """Heuristic to extract CR price from headline strings."""
        import re
        patterns = [
            r"@\s*\$?(\d+\.\d+)",
            r"at\s*\$?(\d+\.\d+)",
            r"\$?(\d+\.\d+)\s*per\s*share"
        ]
        for p in patterns:
            match = re.search(p, headline.lower())
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return 0.0

    def calculate_diff(self, cur: float, cr: float) -> float:
        """Calculate percentage difference between current price and CR price."""
        if not cur or not cr: return 0.0
        return round(((cur - cr) / cr) * 100, 2)

    def _load_overrides(self) -> Dict:
        """Load manual overrides from config/placement_overrides.yaml."""
        path = get_root_dir() / "config" / "placement_overrides.yaml"
        if not path.exists(): return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return {ticker_clean(o["symbol"]): o for o in data.get("overrides", [])}
        except Exception as e:
            logger.error(f"Failed to load overrides: {e}")
            return {}

    def fetch_market_info(self, symbol: str) -> Tuple[Optional[float], Optional[int], Optional[str]]:
        """Fetch current price, market cap, and display name from ASX Header API."""
        try:
            r = self.session.get(PRICE_API.format(symbol.upper()), timeout=DEFAULT_TIMEOUT)
            if r.status_code == 200:
                d = r.json().get("data", {})
                return d.get("priceLast"), d.get("marketCap"), d.get("displayName")
        except:
            pass
        return None, None, None

    def process_raw(self, items: List[Dict]) -> List[Dict]:
        """Heuristic filter for placement announcements."""
        processed = []
        for item in items:
            hl = item.get("headline", "").lower()
            if any(kw in hl for kw in PLACEMENT_KEYWORDS):
                processed.append({
                    "symbol": ticker_clean(item.get("symbol", "")),
                    "date": normalize_date(item.get("date", "")),
                    "company": item.get("companyInfo")[0].get("displayName", "") if item.get("companyInfo") else "",
                    "headline": hl,
                    "pdf_link": item.get("documentKey", "")
                })
        return processed

    def refresh_all_prices(self):
        """Global Update: Fetch current prices for ALL placements in DB."""
        logger.info("Performing Global Price Refresh for all placements...")
        with db.session_scope() as sess:
            all_placements = sess.query(Placement).all()
            if not all_placements: return
            
            symbols = list(set(p.symbol for p in all_placements))
            price_map = {}
            
            with ThreadPoolExecutor(max_workers=20) as ex:
                results = ex.map(lambda s: (s, self.fetch_market_info(s)), symbols)
                for sym, (px, mcap, name) in results:
                    if px is not None:
                        price_map[sym] = {"price": px, "name": name}
            
            updated = 0
            for p in all_placements:
                meta = price_map.get(p.symbol)
                if meta:
                    p.current_price = meta["price"]
                    if meta["name"] and (not p.company or p.company == ""):
                        p.company = meta["name"]
                        
                    if p.cr_price and p.cr_price > 0:
                        p.price_diff_percent = round(((p.current_price - p.cr_price) / p.cr_price) * 100, 2)
                    updated += 1
            logger.info(f"Global Update: Refreshed {updated} records.")

    def sync_to_db(self, events: List[Dict]):
        """Standard sync with overrides and validation."""
        added = 0
        updated = 0
        
        with db.session_scope() as sess:
            valid_stocks = {s.symbol for s in sess.query(Stock).all()}
            
            for ev in events:
                sym = ev["symbol"]
                if sym not in valid_stocks: continue
                
                # Check for exclude override
                ov = self.overrides.get(sym, {})
                if ov.get("exclude"):
                    sess.query(Placement).filter_by(symbol=sym).delete()
                    continue

                # Heuristic for CR Price update (normally would need PDF parsing, 
                # but we use manual overrides or keep existing if same headline)
                cur_px, mcap, live_name = self.fetch_market_info(sym)
                
                # Market Cap Filter
                if mcap and mcap < DEFAULT_MCAP_FILTER:
                    continue

                existing = sess.query(Placement).filter_by(symbol=sym, event_date=datetime.strptime(ev["date"], "%Y-%m-%d").date()).first()
                
                # Priority: Override > Heuristic > Existing
                cr_price = ov.get("cr_price")
                if not cr_price:
                    cr_price = self.extract_cr_price(ev["headline"])
                
                if existing:
                    existing.current_price = cur_px or existing.current_price
                    existing.cr_price = cr_price or existing.cr_price
                    existing.price_diff_percent = self.calculate_diff(existing.current_price, existing.cr_price)
                    updated += 1
                else:
                    try:
                        # Prepare data for PlacementSchema validation
                        diff = self.calculate_diff(cur_px, cr_price)
                        p_data = {
                            "ASX_Code": sym,
                            "Company": ev["company"] or live_name or sym,
                            "Headline": ev["headline"],
                            "Date": ev["date"],
                            "CR_Price": cr_price,
                            "Current_Price": cur_px or 0.0,
                            "Price_Diff_%": diff,
                            "PDF_Link": ev["pdf_link"]
                        }
                        v = PlacementSchema(**p_data)
                        
                        p = Placement(
                            symbol=v.ASX_Code, 
                            company=v.Company, 
                            headline=v.Headline,
                            event_date=v.Date, 
                            cr_price=v.CR_Price, 
                            current_price=v.Current_Price,
                            price_diff_percent=v.Price_Diff_Percent, 
                            pdf_link=v.PDF_Link
                        )
                        sess.add(p)
                        added += 1
                    except Exception as e:
                        logger.error(f"Placement validation failed for {sym}: {e}")

            # --- Forced Overrides for items NOT in current news ---
            for sym, ov in self.overrides.items():
                if ov.get("cr_price"):
                    older = sess.query(Placement).filter_by(symbol=sym).first()
                    if older and older.cr_price != ov["cr_price"]:
                        older.cr_price = ov["cr_price"]
                        if older.current_price and older.cr_price > 0:
                            older.price_diff_percent = round(((older.current_price - older.cr_price) / older.cr_price) * 100, 2)
                        logger.info(f"Forced manual override for {sym}")

        logger.info(f"Sync Complete: Added {added}, Updated {updated}.")

def main():
    parser = argparse.ArgumentParser(description="ASX Placement Scanner")
    parser.add_argument("--months", type=int, default=1)
    parser.add_argument("--full-refresh", action="store_true")
    args = parser.parse_args()

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    
    scanner = PlacementScanner(session)
    
    # 1. Scrape News
    start_date = datetime.now() - timedelta(days=args.months*30)
    
    if not args.full_refresh:
        with db.session_scope() as sess:
            max_dt = sess.query(Placement.event_date).order_by(Placement.event_date.desc()).first()
            if max_dt:
                start_date = datetime.combine(max_dt[0], datetime.min.time())
                logger.info(f"Resuming placements from {start_date:%Y-%m-%d}...")

    params = {
        "dateStart": start_date.strftime("%Y-%m-%d"),
        "dateEnd": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "itemsPerPage": ITEMS_PER_PAGE,
        "page": 0
    }
    
    raw_announcements = []
    while True:
        r = session.get(API_BASE, params=params, timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200: break
        items = r.json().get("data", {}).get("items", [])
        if not items: break
        raw_announcements.extend(items)
        if len(raw_announcements) >= r.json().get("data", {}).get("count", 0): break
        params["page"] += 1
        time.sleep(0.3)

    # 2. Extract & Sync
    events = scanner.process_raw(raw_announcements)
    scanner.sync_to_db(events)
    
    # 3. Global Refresh
    scanner.refresh_all_prices()

if __name__ == "__main__":
    main()
