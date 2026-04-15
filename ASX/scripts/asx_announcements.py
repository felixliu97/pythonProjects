"""
ASX Announcements Scraper (Best Practice Refactor)

Fetches general corporate announcements from the ASX/Markit API, 
performs heuristic rating/summarization, and syncs to PostgreSQL.
"""

import sys
import argparse
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Set

try:
    from db_manager import db
    from db_models import Announcement, Stock
    from db_schemas import AnnouncementSchema
    from utils import logger, load_config, normalize_date, ticker_clean, get_asx_pdf_url, get_sydney_time, get_http_session
except ImportError:
    from scripts.db_manager import db
    from scripts.db_models import Announcement, Stock
    from scripts.db_schemas import AnnouncementSchema
    from scripts.utils import logger, load_config, normalize_date, ticker_clean, get_asx_pdf_url, get_sydney_time, get_http_session

# --- Configuration ---
_CFG = load_config()
_API = _CFG.get("api", {})
API_BASE = _API.get("announcements_base", "https://asx.api.markitdigital.com/asx-research/1.0/markets/announcements")
ITEMS_PER_PAGE = _CFG.get("scanners", {}).get("items_per_page", 1000)

NOISE_KEYWORDS = [
    "appendix 4g", "appendix 3y", "change of director", 
    "becoming a substantial holder", "ceasing to be",
    "notice of meeting", "proxy form", "disclosure notice",
    "shareholder letter", "investor presentation"
]

HIGH_VALUE_KEYWORDS = [
    "assay", "drilling", "results", "high-grade", "discovery",
    "maiden", "resource", "phase 3", "fda", "approval",
    "nickel", "gold", "copper", "uranium", "lithium",
    "exceptional", "breakthrough", "acquisition", "merger",
    "takeover", "binding", "offtake", "definitive"
]

MID_VALUE_KEYWORDS = [
    "trading halt", "placement", "capital rais", "share purchase plan",
    "quarterly", "half year", "annual report", "guidance",
    "production", "revenue", "contract", "agreement", "joint venture",
    "feasibility", "scoping", "update", "progress", "operational"
]

class AnnouncementScanner:
    """Encapsulates the announcement scraping and processing logic."""
    
    def __init__(self, session):
        self.session = session

    def fetch_raw(self, start_date: datetime) -> List[Dict]:
        """Fetch raw announcement JSON from ASX API."""
        end_date = get_sydney_time() + timedelta(days=1)
        
        params = {
            "dateStart": start_date.strftime("%Y-%m-%d"),
            "dateEnd": end_date.strftime("%Y-%m-%d"),
            "itemsPerPage": ITEMS_PER_PAGE,
            "page": 0
        }
        
        all_items = []
        logger.info(f"Fetching announcements (from {start_date.strftime('%Y-%m-%d')})...")
        
        while True:
            try:
                r = self.session.get(API_BASE, params=params, timeout=30)
                r.raise_for_status()
                data = r.json()
                items = data.get("data", {}).get("items", [])
                if not items: break
                
                all_items.extend(items)
                count = data.get("data", {}).get("count", 0)
                if len(all_items) >= count: break
                
                params["page"] += 1
                time.sleep(0.3) # Rate limit respect
            except Exception as e:
                logger.error(f"API fetch failed on page {params['page']}: {e}")
                break
        
        return all_items

    @staticmethod
    def calculate_rating(headline: str, summary: str = "", is_price_sensitive: bool = False) -> int:
        """Heuristic rating engine (1-5).
        
        Scoring:
          - Base: 1 (routine/admin)
          - Price-sensitive flag from API: +2
          - Mid-value keywords (trading halt, placement, quarterly): +1
          - High-value keywords (discovery, assay, approval): +2
        """
        text = (headline + " " + summary).lower()
        rating = 1  # Base for routine filings
        
        # API-sourced signal — strongest single indicator
        if is_price_sensitive:
            rating += 2
        
        # Keyword tiers (additive, not mutually exclusive)
        if any(kw in text for kw in HIGH_VALUE_KEYWORDS):
            rating += 2
        elif any(kw in text for kw in MID_VALUE_KEYWORDS):
            rating += 1
            
        return min(max(rating, 1), 5)

    def process_and_sync(self, raw_items: List[Dict], existing_keys: Set[str]):
        """Filter, validate, and save announcements to the database."""
        added = 0
        skipped = 0
        
        with db.session_scope() as sess:
            # Pre-fetch known stocks for name lookup and auto-registration tracking
            known_stocks = {s.symbol: s.name for s in sess.query(Stock).all()}
            
            for item in raw_items:
                sym = ticker_clean(item.get("symbol", ""))
                hl = item.get("headline", "").strip() # Strip whitespace
                
                # Filters
                if not sym: continue
                if any(nk in hl.lower() for nk in NOISE_KEYWORDS):
                    skipped += 1
                    continue
                
                dt = normalize_date(item.get("date", ""))
                unique_key = f"{sym}_{dt}_{hl[:100]}"
                
                # Pre-filtered check
                if unique_key in existing_keys:
                    continue
                
                # Double check against DB (Case of overlap or near-miss)
                existing_record = sess.query(Announcement).filter_by(unique_key=unique_key).first()
                if existing_record:
                    existing_keys.add(unique_key)
                    # Force update if link is broken (contains asxpdf) or empty
                    if not existing_record.pdf_link or "asxpdf" in existing_record.pdf_link:
                        existing_record.pdf_link = get_asx_pdf_url(item.get("documentKey", ""), dt)
                    continue
                
                try:
                    # Build summary from announcementTypes list
                    ann_types = item.get("announcementTypes", [])
                    summary_text = ", ".join(ann_types) if ann_types else hl
                    
                    is_ps = item.get("isPriceSensitive", False)
                    
                    # 3-tier company name: API companyInfo > stocks table > symbol
                    ci = item.get("companyInfo")
                    if ci and len(ci) > 0 and ci[0].get("displayName"):
                        company_name = ci[0]["displayName"]
                    else:
                        company_name = known_stocks.get(sym, sym)
                    
                    # Auto-register unknown stocks
                    if sym not in known_stocks:
                        new_stock = Stock(symbol=sym, name=company_name, stock_type='announcement')
                        sess.add(new_stock)
                        sess.flush()
                        known_stocks[sym] = company_name
                    
                    # Validate with Schema
                    v = AnnouncementSchema(
                        ASX_Code=sym,
                        Company=company_name,
                        Headline=hl,
                        Summary=summary_text,
                        Date=dt,
                        PDF_Link=get_asx_pdf_url(item.get("documentKey", ""), dt),
                        Rating=self.calculate_rating(hl, summary_text, is_ps)
                    )
                    
                    ann = Announcement(
                        symbol=v.ASX_Code,
                        company=v.Company,
                        headline=v.Headline,
                        summary=v.Summary,
                        event_date=v.Date,
                        pdf_link=v.PDF_Link,
                        rating=v.Rating,
                        unique_key=unique_key
                    )
                    sess.add(ann)
                    added += 1
                except Exception as e:
                    logger.debug(f"Validation failed for announcement {unique_key}: {e}")
                    
        logger.info(f"Sync Complete: Added {added} new announcements (Filtered {skipped} noise items).")

def main():
    parser = argparse.ArgumentParser(description="ASX Announcement Scanner")
    parser.add_argument("--months", type=int, default=1)
    parser.add_argument("--full-refresh", action="store_true")
    args = parser.parse_args()

    session = get_http_session()
    
    scanner = AnnouncementScanner(session)
    existing_keys = set()
    
    # Calculate start_date (Priority: DB Resumption > months argument)
    start_date = get_sydney_time() - timedelta(days=args.months * 30)
    
    if not args.full_refresh:
        with db.session_scope() as sess:
            max_date_row = sess.query(Announcement.event_date).order_by(Announcement.event_date.desc()).first()
            if max_date_row:
                start_date = max_date_row[0]
                logger.info(f"DB check: Resuming from latest date {start_date.strftime('%Y-%m-%d')}")
                
                # Fetch existing keys from the last few days to prevent duplicates during overlap
                recent = sess.query(Announcement.unique_key).filter(
                    Announcement.event_date >= (start_date - timedelta(days=2))
                ).all()
                existing_keys = {r[0] for r in recent}

    raw = scanner.fetch_raw(start_date)
    scanner.process_and_sync(raw, existing_keys)

if __name__ == "__main__":
    main()
