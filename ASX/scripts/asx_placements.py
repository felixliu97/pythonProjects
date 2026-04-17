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
import re
import pdfplumber
from pathlib import Path

try:
    from db_manager import db
    from db_models import Stock, Placement
    from db_schemas import PlacementSchema
    from utils import logger, load_config, normalize_date, get_root_dir, ticker_clean, DEFAULT_TIMEOUT, DEFAULT_MCAP_FILTER, get_asx_pdf_url, get_sydney_time, get_http_session
except ImportError:
    from scripts.db_manager import db
    from scripts.db_models import Stock, Placement
    from scripts.db_schemas import PlacementSchema
    from scripts.utils import logger, load_config, normalize_date, get_root_dir, ticker_clean, DEFAULT_TIMEOUT, DEFAULT_MCAP_FILTER, get_asx_pdf_url, get_sydney_time, get_http_session

# --- Configuration ---
_CFG = load_config()
_API = _CFG.get("api", {})
API_BASE = _API.get("announcements_base", "https://asx.api.markitdigital.com/asx-research/1.0/markets/announcements")
PRICE_API = _API.get("company_header", "https://asx.api.markitdigital.com/asx-research/1.0/companies/{}/header")
ITEMS_PER_PAGE = _CFG.get("ITEMS_PER_PAGE", 1000)

_WORKERS = int(_CFG.get("concurrency", {}).get("placements_workers", 20))

PLACEMENT_KEYWORDS = (
    "placement", "capital rais", "capital raise", "share purchase plan", "spp",
    "equity raising", "entitlement offer", "rights issue"
)

_CACHE_DIR = get_root_dir() / ".pdf_cache"
_CACHE_DIR.mkdir(exist_ok=True)

class PlacementScanner:
    """Encapsulates the capital raising extraction and sync logic."""
    
    def __init__(self, session: requests.Session):
        self.session = session
        self.overrides = self._load_overrides()

    def _download_pdf(self, url: str, filename: str) -> Optional[Path]:
        """Download PDF from URL and save to cache. Returns local path."""
        if not url: return None
        local_path = _CACHE_DIR / filename
        if local_path.exists(): return local_path
        
        try:
            logger.info(f"Downloading PDF: {filename}...")
            r = self.session.get(url, timeout=DEFAULT_TIMEOUT)
            r.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(r.content)
            return local_path
        except Exception as e:
            logger.error(f"Failed to download PDF {filename}: {e}")
            return None

    def _extract_text_from_pdf(self, local_path: Path) -> str:
        """Extract text from the first 2 pages of a PDF."""
        text = ""
        try:
            with pdfplumber.open(local_path) as pdf:
                # First two pages are usually enough for the summary
                for i in range(min(2, len(pdf.pages))):
                    content = pdf.pages[i].extract_text()
                    if content:
                        text += content + "\n"
        except Exception as e:
            logger.error(f"Failed to extract text from {local_path}: {e}")
        return text

    def extract_cr_price(self, text: str) -> float:
        """Heuristic to extract CR price from text (headline or content).
        Avoids picking up total amounts (e.g. $5m) as per-share price.
        """
        if not text: return 0.0
        txt = text.lower()
        
        # 1. Cents Pattern: 15c, 15 cents, 15.5c, 15.5cps
        cent_patterns = [
            r"\b(\d+\.?\d*)\s*(?:c|cents?|cps)\b(?!\s*(?:m|million|b|billion))",
            r"(?:at|@|of)\s*(\d+\.?\d*)\s*(?:c|cents?|cps)",
            r"(?:price|issue|offer)\s*[:]?\s*(?:of|at)?\s*[:]?\s*(\d+\.?\d*)\s*(?:c|cents?|cps)"
        ]
        for p in cent_patterns:
            match = re.search(p, txt)
            if match:
                try:
                    val = float(match.group(1))
                    if val > 1000: continue
                    return round(val / 100.0, 4)
                except ValueError: continue

        # 2. Dollar Patterns (issue price, at $0.15 etc)
        # Use \d+\.?\d* to handle both $1 and $1.50
        dollar_patterns = [
            r"(?:at|@|priced)\s*(?:at)?\s*[:]?\s*\$?\s*(\d+\.\d+)\s*(?:per\s*share|each|a\s+share|\b)",
            r"(?:price|issue|offer)\s*[:]?\s*(?:of|at)?\s*[:]?\s*\$?\s*(\d+\.?\d+)",
            r"\$(\d+\.\d+)\s*per\s*share"
        ]
        for p in dollar_patterns:
            match = re.search(p, txt)
            if match:
                try:
                    val = float(match.group(1))
                    # Sanity check: prices per share are rarely > $500 on ASX
                    if val > 500: continue 
                    return val
                except ValueError: continue

        # 3. Fallback: Simple dollar match with broad negative lookahead
        fallback_patterns = [
            r"\$(\d+\.\d+)\b(?!\s*(?:m|mln|million|b|bln|billion))",
            r"(?:at|@)\s*[:]?\s*(\d+\.\d+)\b(?!\s*(?:c|cent|m|mln|million|b|bln|billion))"
        ]
        for p in fallback_patterns:
            match = re.search(p, txt)
            if match:
                try:
                    val = float(match.group(1))
                    if 0.0001 < val < 500:
                        return val
                except ValueError: continue
            
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
                    "pdf_link": get_asx_pdf_url(item.get("documentKey", ""), item.get("date", "")),
                    "documentKey": item.get("documentKey", "")
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
            
            with ThreadPoolExecutor(max_workers=_WORKERS) as ex:
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
        """Standard sync with overrides and validation.
        
        Pipeline Order (filter-first, extract-later):
        1. Check delete/exclude overrides
        2. Batch-fetch market info for all symbols
        3. Filter by market cap (liquidity gate)
        4. Auto-register unknown stocks with stock_type='announcement'
        5. Only THEN extract CR price (headline -> PDF fallback)
        6. Sync to DB
        """
        added = 0
        updated = 0
        skipped_low_mcap = 0
        
        with db.session_scope() as sess:
            known_stocks = {s.symbol for s in sess.query(Stock).all()}
            
            # --- Phase 1: Apply delete/exclude overrides ---
            eligible_events = []
            for ev in events:
                sym = ev["symbol"]
                ov = self.overrides.get(sym, {})
                if ov.get("delete") or ov.get("exclude"):
                    sess.query(Placement).filter_by(symbol=sym).delete()
                    continue
                eligible_events.append(ev)
            
            # --- Phase 2: Batch-fetch market info for all symbols ---
            unique_symbols = list(set(ev["symbol"] for ev in eligible_events))
            market_cache = {}
            
            with ThreadPoolExecutor(max_workers=_WORKERS) as ex:
                results = ex.map(lambda s: (s, self.fetch_market_info(s)), unique_symbols)
                for sym, (px, mcap, name) in results:
                    market_cache[sym] = {"price": px, "mcap": mcap, "name": name}
            
            # --- Phase 3: Filter by market cap (liquidity gate) ---
            liquid_events = []
            for ev in eligible_events:
                sym = ev["symbol"]
                info = market_cache.get(sym, {})
                mcap = info.get("mcap")
                
                if mcap and mcap < DEFAULT_MCAP_FILTER:
                    skipped_low_mcap += 1
                    continue
                
                # Auto-register unknown stocks
                if sym not in known_stocks:
                    live_name = info.get("name") or ev.get("company") or sym
                    new_stock = Stock(symbol=sym, name=live_name, stock_type='announcement')
                    sess.add(new_stock)
                    sess.flush()
                    known_stocks.add(sym)
                    logger.info(f"Auto-registered new stock: {sym} ({live_name})")
                
                liquid_events.append(ev)
            
            if skipped_low_mcap > 0:
                logger.info(f"Liquidity gate: Skipped {skipped_low_mcap} events (mcap < ${DEFAULT_MCAP_FILTER:,}).")
            
            # --- Phase 4: Extract CR price and sync (only for valid, liquid stocks) ---
            for ev in liquid_events:
                sym = ev["symbol"]
                ov = self.overrides.get(sym, {})
                info = market_cache.get(sym, {})
                cur_px = info.get("price")
                live_name = info.get("name")

                # Find any existing record for this symbol (Deduplication: One stock, one record)
                existing = sess.query(Placement).filter_by(symbol=sym).first()
                
                # Priority: Override > Heuristic
                cr_price = ov.get("cr_price")
                
                # If we already processed this EXACT event successfully, skip extraction
                already_processed = existing and existing.event_date == datetime.strptime(ev["date"], "%Y-%m-%d").date() and existing.cr_price and existing.cr_price > 0
                
                # If no override and not already processed, try extraction (Content > Headline)
                if not cr_price and not already_processed:
                    # 1. Try Headline first (fast)
                    cr_price = self.extract_cr_price(ev["headline"])
                    
                    # 2. If headline failed or looks suspicious, try PDF content
                    if not cr_price or cr_price == 0.0:
                        from utils import get_pdf_filename
                        fname = get_pdf_filename(ev)
                        local_pdf = self._download_pdf(ev["pdf_link"], fname)
                        if local_pdf:
                            content = self._extract_text_from_pdf(local_pdf)
                            if content:
                                cr_price = self.extract_cr_price(content)
                                if cr_price > 0:
                                    logger.info(f"Extracted CR Price {cr_price} from content for {sym}")
                elif already_processed:
                    # Keep the existing price so downstream logic doesn't think we failed
                    cr_price = existing.cr_price
                
                new_date = datetime.strptime(ev["date"], "%Y-%m-%d").date()
                
                if existing:
                    # Priority 1: Manual Overrides always win and update existing
                    if ov.get("cr_price") is not None:
                        existing.cr_price = ov["cr_price"]
                        existing.current_price = cur_px or existing.current_price
                        existing.price_diff_percent = self.calculate_diff(existing.current_price, existing.cr_price)
                        updated += 1
                    else:
                        # Priority 2: Logic for new vs old extraction
                        has_new_price = (cr_price and cr_price > 0)
                        has_old_price = (existing.cr_price and existing.cr_price > 0)
                        
                        should_replace = False
                        if has_new_price and not has_old_price:
                            should_replace = True
                        elif has_new_price == has_old_price: # Both have or both don't
                            if new_date < existing.event_date:
                                should_replace = True
                        
                        # Special Case: If existing price looks like it matched a Total Amount in the headline
                        if has_old_price and not has_new_price:
                            hl_low = existing.headline.lower()
                            if any(x in hl_low for x in ["m", "million", "b", "billion"]):
                                pattern = fr"{re.escape(str(existing.cr_price))}\s*[mb]"
                                if re.search(pattern, hl_low):
                                    existing.cr_price = 0.0
                                    should_replace = True

                        if should_replace:
                            existing.event_date = new_date
                            existing.headline = ev["headline"]
                            existing.cr_price = cr_price
                            existing.pdf_link = ev["pdf_link"]
                            existing.current_price = cur_px or existing.current_price
                            existing.price_diff_percent = self.calculate_diff(existing.current_price, existing.cr_price)
                            updated += 1
                        else:
                            existing.current_price = cur_px or existing.current_price
                            if existing.cr_price and existing.cr_price > 0:
                                existing.price_diff_percent = self.calculate_diff(existing.current_price, existing.cr_price)
                else:
                    try:
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
            logger.info(f"Sync Complete: Added {added}, Updated {updated}.")

    def apply_forced_overrides(self):
        """Handle manual overrides (price updates and deletions) globally for all matched symbols.
        This ensures that symbols not in the current news scrape are also updated or removed.
        """
        logger.info("Applying global forced overrides...")
        with db.session_scope() as sess:
            for sym, ov in self.overrides.items():
                # 1. Handle Deletions
                if ov.get("delete") or ov.get("exclude"):
                    count = sess.query(Placement).filter_by(symbol=sym).delete()
                    if count > 0:
                        logger.info(f"Globally excluded/deleted: {sym}")
                    continue

                # 2. Handle Price Overrides
                if ov.get("cr_price"):
                    older = sess.query(Placement).filter_by(symbol=sym).first()
                    if older and older.cr_price != ov["cr_price"]:
                        older.cr_price = ov["cr_price"]
                        if older.current_price and older.cr_price > 0:
                            older.price_diff_percent = self.calculate_diff(older.current_price, older.cr_price)
                        logger.info(f"Forced manual price override: {sym} -> {ov['cr_price']}")


def main():
    parser = argparse.ArgumentParser(description="ASX Placement Scanner")
    parser.add_argument("--months", type=int, default=0)
    parser.add_argument("--full-refresh", action="store_true")
    args = parser.parse_args()

    session = get_http_session()
    
    scanner = PlacementScanner(session)
    
    # 1. Scrape News
    start_date = get_sydney_time() - timedelta(days=args.months*30)
    
    if not args.full_refresh:
        with db.session_scope() as sess:
            max_dt = sess.query(Placement.event_date).order_by(Placement.event_date.desc()).first()
            if max_dt:
                db_date = datetime.combine(max_dt[0], datetime.min.time())
                # Use the more recent of DB date and (today - 2 days)
                # to avoid re-processing old data when no new placements were found
                recent_cutoff = get_sydney_time() - timedelta(days=2)
                start_date = max(db_date, recent_cutoff.replace(tzinfo=None))
                logger.info(f"Resuming placements from {start_date:%Y-%m-%d}...")

    params = {
        "dateStart": start_date.strftime("%Y-%m-%d"),
        "dateEnd": (get_sydney_time() + timedelta(days=1)).strftime("%Y-%m-%d"),
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
    
    # 3. Global Forced Overrides (Sync database with YAML state)
    scanner.apply_forced_overrides()
    
    # 4. Global Refresh (Fetch latest market prices)
    scanner.refresh_all_prices()

if __name__ == "__main__":
    main()
