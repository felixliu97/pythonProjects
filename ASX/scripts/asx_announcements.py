"""
ASX Price Sensitive Announcements Scanner (Refactored)

Scans ASX announcements for price-sensitive events, downloads PDFs, 
extracts summaries, and syncs to PostgreSQL database.
"""

import argparse
import io
import os
import re
import string
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
import json
import requests
from sqlalchemy import func

# Local Imports
try:
    from db_manager import db
    from db_models import Stock, Announcement
    from db_schemas import AnnouncementSchema
    from utils import logger, load_config, normalize_date, get_root_dir
except ImportError:
    from scripts.db_manager import db
    from scripts.db_models import Stock, Announcement
    from scripts.db_schemas import AnnouncementSchema
    from scripts.utils import logger, load_config, normalize_date, get_root_dir

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logger.warning("pdfplumber not installed. PDF analysis disabled.")

# --- Configuration ---
_CFG = load_config()
API_BASE = _CFG["API_BASE"]
HEADER_API = _CFG["HEADER_API"]
PDF_CDN = _CFG["PDF_CDN"]
PDF_TOKEN = _CFG["PDF_TOKEN"]
ITEMS_PER_PAGE = _CFG["ITEMS_PER_PAGE"]

NOISE_KEYWORDS = (
    "trading halt", "pausing in trading", "pause in trading", 
    "response to asx", "price query", "notification of buy-back",
    "suspension from quotation", "cleansing notice", "market update",
    "on-market share buyback", "on-market buy-back", "investor presentation",
    "disclosure document", "dividend/distribution", "investor webinar presentation"
)

def load_existing_from_db() -> Tuple[Optional[str], Set[str]]:
    """Loads max date and existing unique keys from DB to prevent duplicates."""
    existing_keys = set()
    max_date = None

    try:
        session = db.get_session()
        max_date_res = session.query(func.max(Announcement.event_date)).scalar()
        if max_date_res:
            max_date = max_date_res.strftime("%Y-%m-%d")
        
        # Get all unique_keys
        keys = session.query(Announcement.unique_key).all()
        existing_keys = {k[0] for k in keys}
        
    except Exception as e:
        logger.warning(f"Could not read from DB: {e}")
        return None, set()

    return max_date, existing_keys

def fetch_announcements(months: int = 2, start_override: Optional[str] = None) -> List[Dict]:
    """Fetches raw announcement items from ASX API."""
    end_date = datetime.now() + timedelta(days=1)
    if start_override:
        start_date = datetime.strptime(start_override, "%Y-%m-%d")
    else:
        start_date = end_date - timedelta(days=months * 30)

    params = {
        "dateStart": start_date.strftime("%Y-%m-%d"),
        "dateEnd": end_date.strftime("%Y-%m-%d"),
        "itemsPerPage": ITEMS_PER_PAGE,
        "priceSensitiveOnly": "true"
    }

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    all_items = []
    page = 0
    logger.info(f"Fetching ASX price-sensitive announcements ({start_date:%Y-%m-%d} -> {end_date:%Y-%m-%d})...")

    while True:
        params["page"] = page
        try:
            r = session.get(API_BASE, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            logger.error(f"API Request failed: {e}")
            break

        items = data.get("data", {}).get("items", [])
        total = data.get("data", {}).get("count", 0)
        if not items: break

        all_items.extend(items)
        # Update line (using direct print for progress bar)
        print(f"\r  Fetched {len(all_items)}/{total} announcements...", end="", flush=True)
        if len(all_items) >= total: break
        page += 1
        time.sleep(0.3)
    
    print() # New line after loop
    return all_items

def fetch_company_name(symbol: str, session: requests.Session) -> Tuple[str, str]:
    """Fetch company display name from ASX header API."""
    url = HEADER_API.format(symbol)
    try:
        r = session.get(url, timeout=10)
        if r.status_code == 200:
            dn = r.json().get("data", {}).get("displayName", "")
            if dn: return symbol, dn
    except: pass
    return symbol, ""

def process_event(event: Dict, session: requests.Session, pdf_dir: str, no_pdf: bool) -> Dict:
    """Processes a single event: downloads PDF and extracts keywords/summaries."""
    ev = event.copy()
    if no_pdf or not PDF_SUPPORT or not ev.get("doc_keys"):
        return ev
    
    doc_key = ev["doc_keys"][0]
    pdf_url = f"{PDF_CDN}{doc_key}?access_token={PDF_TOKEN}"
    local_pdf = os.path.join(pdf_dir, f"{doc_key}.pdf")

    # Download if not exists
    if not os.path.exists(local_pdf):
        try:
            r = session.get(pdf_url, timeout=20)
            if r.status_code == 200:
                with open(local_pdf, 'wb') as f:
                    f.write(r.content)
        except: pass
    
    # Extract Text
    if os.path.exists(local_pdf):
        try:
            with pdfplumber.open(local_pdf) as pdf:
                full_text = []
                for page in pdf.pages[:3]: # Scan first 3 pages
                    full_text.append(page.extract_text() or "")
                text = " ".join(full_text).lower()
                
                # Simple summary extraction (first sentence of body)
                summary_match = re.search(r'(?i)(?:overview|summary|highlights|announcement)\s*(.*?\.)', text)
                if summary_match:
                    ev["summary"] = summary_match.group(1).capitalize()
        except: pass

    return ev

def save_to_db(new_events: List[Dict]) -> None:
    """Validate and save new events to the database using Pydantic schemas."""
    count = 0
    session = db.get_session()
    
    for ev in new_events:
        try:
            symbol = ev.get("symbol")
            event_date = ev.get("date")
            headline = ev.get("headline", "")
            
            # Re-calculate unique_key (consistent with main duplication logic)
            unique_key = f"{symbol}_{event_date}_{headline[:100]}"
            
            # Map scraper dict to Schema for validation
            schema_input = {
                "ASX_Code": symbol,
                "Company": ev.get("company", ""),
                "Headline": headline,
                "Date": event_date,
                "Summary": ev.get("summary") or "",
                "PDF_Link": ev.get("pdf_link") or (f"{PDF_CDN}{ev['doc_keys'][0]}?access_token={PDF_TOKEN}" if ev.get("doc_keys") else ""),
                "Rating": ev.get("rating") or 2
            }
            v_ann = AnnouncementSchema(**schema_input)
            
            ann = Announcement(
                symbol=v_ann.ASX_Code,
                company=v_ann.Company,
                headline=v_ann.Headline,
                event_date=v_ann.Date,
                summary=v_ann.Summary,
                pdf_link=v_ann.PDF_Link,
                rating=v_ann.Rating,
                unique_key=unique_key
            )
            session.add(ann)
            count += 1
        except Exception as e:
            logger.debug(f"Validation skipped for item: {e}")
    
    session.commit()
    logger.info(f"DB Sync: Added {count} new announcements to PostgreSQL.")

def main() -> None:
    parser = argparse.ArgumentParser(description="ASX Announcements Scanner")
    parser.add_argument("--months", type=int, default=2)
    parser.add_argument("--no-pdf", action="store_true")
    parser.add_argument("--full-refresh", action="store_true")
    args = parser.parse_args()

    root_dir = get_root_dir()
    pdf_dir = root_dir / ".pdf_cache"
    pdf_dir.mkdir(exist_ok=True)

    session_req = requests.Session()
    session_req.headers.update({"User-Agent": "Mozilla/5.0"})

    existing_keys = set()
    start_override = None

    if not args.full_refresh:
        max_date, existing_keys = load_existing_from_db()
        if max_date:
            start_override = max_date
            logger.info(f"Resuming announcements from {max_date}...")
    
    raw_items = fetch_announcements(args.months, start_override)
    events_map = {}
    
    for item in raw_items:
        hl = item.get("headline", "")
        if any(nk in hl.lower() for nk in NOISE_KEYWORDS): continue
        sym = item.get("symbol", "")
        if not sym: continue
        
        date_display = normalize_date(item.get("date", ""))
        dedup_key = f"{sym}_{date_display}_{hl[:100]}"
        if dedup_key in existing_keys: continue
        
        doc_key = item.get("documentKey", "")
        if dedup_key not in events_map:
            events_map[dedup_key] = {
                "symbol": sym, "date": date_display, "company": "",
                "headline": hl, "doc_keys": [doc_key] if doc_key else []
            }
        else:
            if doc_key and doc_key not in events_map[dedup_key]["doc_keys"]:
                events_map[dedup_key]["doc_keys"].append(doc_key)

    events_list = list(events_map.values())
    if not events_list:
        logger.info("No new announcements found.")
        return

    logger.info(f"Processing {len(events_list)} new announcements...")
    new_events = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_event, ev, session_req, str(pdf_dir), args.no_pdf): ev for ev in events_list}
        for future in as_completed(futures):
            new_events.append(future.result())

    # Fetch names for new companies if missing
    symbols_to_fetch = list({ev["symbol"] for ev in new_events if not ev.get("company")})
    if symbols_to_fetch:
        logger.info(f"Fetching names for {len(symbols_to_fetch)} symbols...")
        name_map = {}
        with ThreadPoolExecutor(max_workers=20) as executor:
            for sym, dname in executor.map(lambda s: fetch_company_name(s, session_req), symbols_to_fetch):
                if dname: name_map[sym] = dname
        for ev in new_events:
            if ev["symbol"] in name_map: ev["company"] = name_map[ev["symbol"]]

    save_to_db(new_events)

if __name__ == "__main__":
    main()
