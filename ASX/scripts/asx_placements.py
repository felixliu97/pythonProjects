"""
ASX Placement / Capital Raising Scanner (Refactored)

Scans ASX announcements for capital raising events, extracts financial details,
fetches live prices, and syncs to PostgreSQL database.
"""

import argparse
import io
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
import json
import requests
import yfinance as yf
from sqlalchemy import func

# Local Imports
try:
    from db_manager import db
    from db_models import Stock, Placement
    from db_schemas import PlacementSchema
    from utils import logger, load_config, normalize_date, get_root_dir, ticker_clean
except ImportError:
    from scripts.db_manager import db
    from scripts.db_models import Stock, Placement
    from scripts.db_schemas import PlacementSchema
    from scripts.utils import logger, load_config, normalize_date, get_root_dir, ticker_clean

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logger.warning("pdfplumber not installed. PDF analysis disabled.")

# --- Configuration ---
_CFG = load_config()
API_BASE = _CFG["API_BASE"]
PRICE_API = _CFG["HEADER_API"]
PDF_CDN = _CFG["PDF_CDN"]
PDF_TOKEN = _CFG["PDF_TOKEN"]
ITEMS_PER_PAGE = _CFG["ITEMS_PER_PAGE"]

PLACEMENT_KEYWORDS = (
    "placement", "capital rais", "capital raise", "share purchase plan", "spp",
    "rights issue", "entitlement offer", "equity rais", "equity raise", "pro rata",
    "non-renounceable", "renounceable offer",
)
NOISE_TYPES = ("cleansing notice", "application for quotation", "appendix 2a", "change of director", "results of meeting", "notification of buy-back",)
REJECT_KEYWORDS = ("acquisition", "takeover", "merger", "exercise of options", "conversion", "dividend", "buy-back", "vesting", "lapse", "cancellation",)

def load_existing_from_db() -> Optional[str]:
    """Loads the latest placement date from DB to allow incremental sync."""
    try:
        session = db.get_session()
        max_date = session.query(func.max(Placement.event_date)).scalar()
        return max_date.strftime("%Y-%m-%d") if max_date else None
    except Exception as e:
        logger.warning(f"Could not read max date from DB: {e}")
        return None

def is_placement(headline: str, ann_types: List[str]) -> bool:
    """Filter logic to identify capital raising announcements."""
    hl = headline.lower()
    types_str = " ".join(ann_types).lower()
    if any(nt in types_str for nt in NOISE_TYPES): return False
    if any(rk in hl for rk in REJECT_KEYWORDS): return False
    if any(kw in hl for kw in PLACEMENT_KEYWORDS): return True
    if any(kw in types_str for kw in ("placement", "spp", "rights issue")): return True
    return False

def extract_price(text: str) -> Optional[float]:
    """Extract placement price using regex from cleaned text block."""
    patterns = [
        r'\$(\d+\.?\d*)\s*(?:per|each|at an issue price of)',
        r'issue price of\s*\$?(\d+\.?\d*)',
        r'at\s*\$?(\d+\.?\d*)\s*per'
    ]
    for p in patterns:
        m = re.search(p, text.lower())
        if m:
            try: return float(m.group(1))
            except: pass
    return None

def fetch_current_info(symbol: str, session: requests.Session) -> Tuple[str, Optional[float], Optional[str]]:
    """Fetch live price and company name."""
    url = PRICE_API.format(symbol)
    try:
        r = session.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", {})
            price = data.get("priceLast")
            name = data.get("displayName")
            return symbol, price, name
    except: pass
    return symbol, None, None

def process_event(event: Dict, session: requests.Session, cache_dir: str, no_pdf: bool) -> Dict:
    """Download and analyze PDF for CR_Price."""
    ev = event.copy()
    if no_pdf or not PDF_SUPPORT or not ev.get("doc_keys"):
        return ev
    
    doc_key = ev["doc_keys"][0]
    pdf_path = os.path.join(cache_dir, f"{doc_key}.pdf")
    
    if not os.path.exists(pdf_path):
        try:
            r = session.get(f"{PDF_CDN}{doc_key}?access_token={PDF_TOKEN}", timeout=20)
            if r.status_code == 200:
                with open(pdf_path, 'wb') as f: f.write(r.content)
        except: pass
        
    if os.path.exists(pdf_path):
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = " ".join(p.extract_text() or "" for p in pdf.pages[:3])
                ev["CR_Price"] = extract_price(text)
        except: pass
    return ev

def fetch_liquidity_info(symbol: str) -> Tuple[bool, str]:
    """Verify if a stock is 'liquid' enough (Market Cap > 15M)."""
    try:
        ticker = yf.Ticker(f"{symbol}.AX")
        info = ticker.fast_info
        mc = info.get("market_cap", 0)
        if mc < 15_000_000:
            return False, f"Small Cap (${mc/1e6:.1f}M)"
        return True, ""
    except:
        return True, "Unknown"

def save_to_db(all_events: List[Dict], price_map: Dict, name_map: Dict) -> None:
    """Validate and upsert placement records."""
    session_db = db.get_session()
    added, updated = 0, 0

    # Sort by date ascending to ensure later ones overwrite earlier ones during the loop
    all_events.sort(key=lambda x: x.get("date", ""), reverse=False)

    for ev in all_events:
        try:
            sym = ev.get("symbol")
            schema_input = {
                "ASX_Code": sym,
                "Company": ev.get("company") or name_map.get(sym, ""),
                "Headline": ev.get("headline", ""),
                "Date": ev.get("date"),
                "CR_Price": ev.get("CR_Price"),
                "Current_Price": price_map.get(sym),
                "Price_Diff_%": 0, # Validator handles calculation or dummy
                "PDF_Link": ev.get("PDF_Link") or (f"{PDF_CDN}{ev['doc_keys'][0]}?access_token={PDF_TOKEN}" if ev.get("doc_keys") else "")
            }
            v_plac = PlacementSchema(**schema_input)
            
            # Final calculation
            diff = None
            if v_plac.Current_Price and v_plac.CR_Price and v_plac.CR_Price > 0:
                diff = round(((v_plac.Current_Price - v_plac.CR_Price) / v_plac.CR_Price) * 100, 2)

            existing = session_db.query(Placement).filter_by(asx_code=v_plac.ASX_Code).first()
            if existing:
                # Update if the new event is the same date or newer
                if v_plac.Date >= existing.event_date:
                    existing.headline = v_plac.Headline
                    existing.event_date = v_plac.Date
                    existing.cr_price = v_plac.CR_Price or existing.cr_price
                    existing.pdf_link = v_plac.PDF_Link or existing.pdf_link
                
                existing.current_price = v_plac.Current_Price or existing.current_price
                existing.price_diff_percent = diff or existing.price_diff_percent
                updated += 1
            else:
                p_new = Placement(
                    symbol=v_plac.ASX_Code,
                    company=v_plac.Company,
                    headline=v_plac.Headline,
                    event_date=v_plac.Date,
                    cr_price=v_plac.CR_Price,
                    current_price=v_plac.Current_Price,
                    price_diff_percent=diff,
                    pdf_link=v_plac.PDF_Link
                )
                session_db.add(p_new)
                added += 1
        except Exception as e:
            logger.debug(f"Placement validation skipped: {e}")

    session_db.commit()
    logger.info(f"DB Sync: Added {added}, Updated {updated} placements.")

def main():
    parser = argparse.ArgumentParser(description="ASX Placement Scanner")
    parser.add_argument("--months", type=int, default=2)
    parser.add_argument("--no-pdf", action="store_true")
    parser.add_argument("--full-refresh", action="store_true")
    args = parser.parse_args()

    root_dir = get_root_dir()
    cache_dir = root_dir / ".pdf_cache"
    cache_dir.mkdir(exist_ok=True)

    # Scrape Logic with Pagination
    start_date = datetime.now() - timedelta(days=args.months*30)
    
    if not args.full_refresh:
        max_db_date = load_existing_from_db()
        if max_db_date:
            start_date = datetime.strptime(max_db_date, "%Y-%m-%d")
            logger.info(f"Resuming placements from {max_db_date}...")

    end_date = datetime.now() + timedelta(days=1)
    
    params = {
        "dateStart": start_date.strftime("%Y-%m-%d"), 
        "dateEnd": end_date.strftime("%Y-%m-%d"), 
        "itemsPerPage": ITEMS_PER_PAGE
    }
    
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    
    raw_items = []
    page = 0
    logger.info(f"Fetching ASX announcements for placements ({start_date:%Y-%m-%d} -> {end_date:%Y-%m-%d})...")
    
    while True:
        params["page"] = page
        try:
            r = session.get(API_BASE, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            logger.error(f"Failed to fetch data on page {page}: {e}")
            break

        items = data.get("data", {}).get("items", [])
        total = data.get("data", {}).get("count", 0)
        if not items: break

        raw_items.extend(items)
        print(f"\r  Fetched {len(raw_items)}/{total} announcements...", end="", flush=True)
        
        if len(raw_items) >= total: break
        page += 1
        time.sleep(0.3)
    
    print() # New line after status

    events = {}
    for item in raw_items:
        sym, hl, types = item.get("symbol", ""), item.get("headline", ""), item.get("announcementTypes", [])
        if not sym or not is_placement(hl, types): continue
        
        date_display = normalize_date(item.get("date", ""))
        event_key = f"{sym}_{date_display}"
        doc_key = item.get("documentKey", "")
        
        if event_key not in events:
            comp_info = item.get("companyInfo", [])
            events[event_key] = {"symbol": sym, "date": date_display, "company": comp_info[0].get("displayName", "") if comp_info else "", "headline": hl, "doc_keys": [doc_key] if doc_key else []}
        else:
            if doc_key and doc_key not in events[event_key]["doc_keys"]: events[event_key]["doc_keys"].append(doc_key)

    events_list = list(events.values())
    if not events_list:
        logger.info("No placement activity detected.")
        return

    logger.info(f"Analyzing {len(events_list)} potential placements...")
    processed = []
    with ThreadPoolExecutor(max_workers=min(20, len(events_list))) as ex:
        processed = list(ex.map(lambda ev: process_event(ev, session, str(cache_dir), args.no_pdf), events_list))
    
    # Filter by market cap (quality filter)
    logger.info(f"Verifying market liquidity...")
    final_processed = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        results = ex.map(lambda ev: (ev, fetch_liquidity_info(ev["symbol"])), processed)
        for ev, (is_liquid, reason) in results:
            if is_liquid: final_processed.append(ev)

    # Fetch Prices
    logger.info(f"Updating market prices...")
    price_map, name_map = {}, {}
    unique_symbols = [ev["symbol"] for ev in final_processed]
    with ThreadPoolExecutor(max_workers=20) as ex:
        for sym, px, dname in ex.map(lambda s: fetch_current_info(s, session), unique_symbols):
            if px is not None: price_map[sym] = px
            if dname: name_map[sym] = dname

    save_to_db(final_processed, price_map, name_map)

if __name__ == "__main__":
    main()
