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
from pathlib import Path

try:
    from db_manager import db
    from db_models import Announcement, Stock
    from db_schemas import AnnouncementSchema
    from utils import logger, load_config, normalize_date, ticker_clean, get_asx_pdf_url, get_sydney_time, get_http_session, get_root_dir, get_pdf_filename
except ImportError:
    from scripts.db_manager import db
    from scripts.db_models import Announcement, Stock
    from scripts.db_schemas import AnnouncementSchema
    from scripts.utils import logger, load_config, normalize_date, ticker_clean, get_asx_pdf_url, get_sydney_time, get_http_session, get_root_dir, get_pdf_filename

# --- Configuration ---
_CFG = load_config()
_API = _CFG.get("api", {})
API_BASE = _API.get("announcements_base", "https://asx.api.markitdigital.com/asx-research/1.0/markets/announcements")
ITEMS_PER_PAGE = _CFG.get("scanners", {}).get("items_per_page", 1000)

_CACHE_DIR = get_root_dir() / ".pdf_cache"
_CACHE_DIR.mkdir(exist_ok=True)


NOISE_KEYWORDS = [
    "appendix 4g", "appendix 3y", "change of director", 
    "becoming a substantial holder", "ceasing to be",
    "notice of meeting", "proxy form", "disclosure notice",
    "shareholder letter", "investor presentation"
]

HIGH_VALUE_KEYWORDS = [
    "assay", "drilling", "high-grade", "discovery",
    "maiden", "resource", "phase 3", "fda", "approval",
    "exceptional", "breakthrough", "acquisition", "merger",
    "takeover", "binding", "offtake", "definitive", "feasibility study",
    "term sheet"
]

STRONG_CATALYST_PHRASES = [
    "high-grade assay results",
    "maiden resource estimate",
    "maiden mre",
    "resource estimate",
    "definitive feasibility study",
    "dfs results",
    "binding agreement",
    "binding offtake",
    "fda approval",
    "trial results",
    "phase 3 results",
    "massive sulphides",
    "significant discovery",
    "exceptional intercepts",
    "high-grade discovery",
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

    def _download_pdf(self, url: str, filename: str) -> Optional[Path]:
        """Download PDF to cache if not already present. Returns local path."""
        if not url: return None
        local_path = _CACHE_DIR / filename
        if local_path.exists(): return local_path
        try:
            logger.info(f"Downloading PDF: {filename}...")
            r = self.session.get(url, timeout=30)
            r.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(r.content)
            return local_path
        except Exception as e:
            logger.error(f"Failed to download PDF {filename}: {e}")
            return None

    def fetch_raw(self, start_date: datetime, *, price_sensitive_only: bool = True) -> List[Dict]:
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

                if price_sensitive_only:
                    items = [
                        it
                        for it in items
                        if bool(it.get("isPriceSensitive") or it.get("priceSensitive") or False)
                    ]
                
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
    def _load_rating_cfg() -> Dict:
        cfg = _CFG.get("announcement_rating", {})
        return {
            "price_sensitive_bonus": int(cfg.get("price_sensitive_bonus", 1)),
            "strong_phrase_bonus": int(cfg.get("strong_phrase_bonus", 3)),
            "high_keyword_bonus": int(cfg.get("high_keyword_bonus", 2)),
            "mid_keyword_bonus": int(cfg.get("mid_keyword_bonus", 1)),
            "progress_cap": int(cfg.get("progress_cap", 4)),
            "all_caps_force_5": bool(cfg.get("all_caps_force_5", True)),
            "all_caps_min_alpha": int(cfg.get("all_caps_min_alpha", 10)),
            "strong_catalyst_phrases": cfg.get("strong_catalyst_phrases", STRONG_CATALYST_PHRASES),
            "high_value_keywords": cfg.get("high_value_keywords", HIGH_VALUE_KEYWORDS),
            "mid_value_keywords": cfg.get("mid_value_keywords", MID_VALUE_KEYWORDS),
        }

    @staticmethod
    def _is_all_caps_headline(headline: str, *, min_alpha: int) -> bool:
        if not headline:
            return False
        alpha = [c for c in headline if c.isalpha()]
        if len(alpha) < min_alpha:
            return False
        if any(c.islower() for c in alpha):
            return False
        return True

    @staticmethod
    def calculate_rating(headline: str, summary: str = "", is_price_sensitive: bool = False) -> int:
        rating, _ = AnnouncementScanner.calculate_rating_with_reason(headline, summary, is_price_sensitive)
        return rating

    @staticmethod
    def calculate_rating_with_reason(
        headline: str,
        summary: str = "",
        is_price_sensitive: bool = False,
    ) -> tuple[int, str]:
        cfg = AnnouncementScanner._load_rating_cfg()
        import re

        text = (headline + " " + summary).lower()
        rating = 1
        reasons: List[str] = []

        # 1. Price Sensitive Bonus
        if is_price_sensitive:
            rating += cfg["price_sensitive_bonus"]
            reasons.append("price_sensitive")

        # 2. Data Impact Bonus (Regex for grades like 150g/t or 2.5%)
        if re.search(r"\d+(\.\d+)?\s*(g/t|%)", text):
            rating += 1
            reasons.append("impact_data")

        # 3. Phrase/Keyword Scoring
        strong_phrases = cfg["strong_catalyst_phrases"] or []
        high_keywords = cfg["high_value_keywords"] or []
        mid_keywords = cfg["mid_value_keywords"] or []

        strong_hit = any(ph in text for ph in strong_phrases)
        if strong_hit:
            rating += cfg["strong_phrase_bonus"]
            reasons.append("strong_phrase")
        elif any(kw in text for kw in high_keywords):
            rating += cfg["high_keyword_bonus"]
            reasons.append("high_keyword")
        elif any(kw in text for kw in mid_keywords):
            rating += cfg["mid_keyword_bonus"]
            reasons.append("mid_keyword")

        if ("progress report" in text or "exploration update" in text) and not strong_hit:
            if rating > cfg["progress_cap"]:
                rating = cfg["progress_cap"]
                reasons.append("progress_cap")

        if cfg["all_caps_force_5"] and AnnouncementScanner._is_all_caps_headline(
            headline,
            min_alpha=cfg["all_caps_min_alpha"],
        ):
            rating = 5
            reasons.append("all_caps")

        rating = min(max(int(rating), 1), 5)
        return rating, ";".join(reasons)

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
                    
                # Strict Security Type Filter: Only allow Ordinary Stocks & ETFs
                ci = item.get("companyInfo")
                if ci and len(ci) > 0:
                    issue_type = ci[0].get("issueType", "")
                    # CS=Common Stock, CD=CDI, ET=ETF, UI=Units
                    if issue_type and issue_type not in ["CS", "CD", "ET", "UI"]:
                        skipped += 1
                        continue
                    
                    # Filter out derivatives/bonds with long tickers (e.g., SPPHA, CBAHB)
                    real_sym = ci[0].get("symbol", "")
                    if real_sym and len(real_sym.replace('.AX', '')) > 4:
                        skipped += 1
                        continue
                        
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
                    # Download PDF for existing price-sensitive announcements with rating > 3
                    is_ps = bool(item.get("isPriceSensitive") or item.get("priceSensitive") or False)
                    if is_ps and existing_record.rating and existing_record.rating > 3 and existing_record.pdf_link:
                        pdf_ev = {"date": dt, "symbol": sym, "headline": hl}
                        self._download_pdf(existing_record.pdf_link, get_pdf_filename(pdf_ev))
                    continue
                
                try:
                    # Build summary from announcementTypes list
                    ann_types = item.get("announcementTypes", [])
                    summary_text = ", ".join(ann_types) if ann_types else hl
                    
                    is_ps = bool(item.get("isPriceSensitive") or item.get("priceSensitive") or False)

                    rating, rating_reason = self.calculate_rating_with_reason(hl, summary_text, is_ps)
                    rating_reason = rating_reason or ""
                    
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
                        Rating=rating,
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
                    
                    # Download PDF for price-sensitive announcements with rating > 3
                    if is_ps and rating > 3 and v.PDF_Link:
                        pdf_ev = {"date": dt, "symbol": sym, "headline": hl}
                        self._download_pdf(v.PDF_Link, get_pdf_filename(pdf_ev))
                except Exception as e:
                    logger.debug(f"Validation failed for announcement {unique_key}: {e}")
                    
        logger.info(f"Sync Complete: Added {added} new announcements (Filtered {skipped} noise items).")

    def recalc_and_update(self, raw_items: List[Dict]) -> None:
        """Recompute rating/rating_reason for announcements and update DB rows if they exist."""
        updated = 0
        skipped = 0
        with db.session_scope() as sess:
            for item in raw_items:
                sym = ticker_clean(item.get("symbol", ""))
                hl = item.get("headline", "").strip()

                if not sym or not hl:
                    continue
                if any(nk in hl.lower() for nk in NOISE_KEYWORDS):
                    skipped += 1
                    continue

                dt = normalize_date(item.get("date", ""))
                unique_key = f"{sym}_{dt}_{hl[:100]}"

                ann = sess.query(Announcement).filter_by(unique_key=unique_key).first()
                if not ann:
                    continue

                ann_types = item.get("announcementTypes", [])
                summary_text = ", ".join(ann_types) if ann_types else (ann.summary or hl)
                is_ps = bool(item.get("isPriceSensitive") or item.get("priceSensitive") or False)

                rating, _ = self.calculate_rating_with_reason(hl, summary_text, is_ps)

                ann.rating = rating
                if not ann.pdf_link or "asxpdf" in (ann.pdf_link or ""):
                    ann.pdf_link = get_asx_pdf_url(item.get("documentKey", ""), dt)
                updated += 1

                # Download PDF for price-sensitive announcements with rating > 3
                if is_ps and rating > 3 and ann.pdf_link:
                    pdf_ev = {"date": dt, "symbol": sym, "headline": hl}
                    self._download_pdf(ann.pdf_link, get_pdf_filename(pdf_ev))

        logger.info(f"Recalc Complete: Updated {updated} announcements (Filtered {skipped} noise items).")

def main():
    parser = argparse.ArgumentParser(description="ASX Announcement Scanner")
    parser.add_argument("--months", type=int, default=0)
    parser.add_argument("--full-refresh", action="store_true")
    parser.add_argument("--recalc-days", type=int, default=0, help="Recalculate rating/rating_reason for the last N days of announcements fetched")
    parser.add_argument("--all-announcements", action="store_true", help="Fetch all announcements (otherwise only price-sensitive)")
    args = parser.parse_args()

    session = get_http_session()
    
    scanner = AnnouncementScanner(session)
    existing_keys = set()
    
    # Calculate start_date (Priority: DB Resumption > months argument)
    start_date = get_sydney_time() - timedelta(days=args.months * 30)
    if args.recalc_days and args.recalc_days > 0:
        start_date = get_sydney_time() - timedelta(days=args.recalc_days)
    
    if not args.full_refresh and not (args.recalc_days and args.recalc_days > 0):
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

    raw = scanner.fetch_raw(start_date, price_sensitive_only=not args.all_announcements)
    if args.recalc_days and args.recalc_days > 0:
        scanner.recalc_and_update(raw)
    scanner.process_and_sync(raw, existing_keys)

if __name__ == "__main__":
    main()
