"""
ASX Placement / Capital Raising Scanner

Scans ASX announcements for capital raising events, deduplicates by symbol
and date, extracts financial details from PDFs (multi-threaded), fetches
real-time prices, and outputs to YAML and JSON.
"""

import argparse
import io
import os
import re
import string
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

import yaml
import requests
import html
import yfinance as yf
import json

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

class _C:
    R=chr(27)+'[0m'; DIM=chr(27)+'[2m'; GREEN=chr(27)+'[92m'
    YELLOW=chr(27)+'[93m'; BOLD=chr(27)+'[1m'
def _ok(m):   print(f"{_C.GREEN}{m}{_C.R}")
def _warn(m): print(f"{_C.YELLOW}{m}{_C.R}")
def _dim(m):  print(f"{_C.DIM}{m}{_C.R}",  end="", flush=True)
def _info(m): print(f"{_C.DIM}{m}{_C.R}")

# ── Constants ────────────────────────────────────────────────────────────────
# ── Configuration ────────────────────────────────────────────────────────────
def load_config():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    settings_path = os.path.join(root_dir, "config", "settings.yaml")
    cfg = {}
    if os.path.exists(settings_path):
        with open(settings_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    
    api = cfg.get("api", {})
    scanners = cfg.get("scanners", {})
    
    return {
        "API_BASE": api.get("announcements_base", "https://asx.api.markitdigital.com/asx-research/1.0/markets/announcements"),
        "PRICE_API": api.get("company_header", "https://asx.api.markitdigital.com/asx-research/1.0/companies/{}/header"),
        "PDF_CDN": api.get("pdf_cdn", "https://cdn-api.markitdigital.com/apiman-gateway/ASX/asx-research/1.0/file/"),
        "PDF_TOKEN": api.get("pdf_token", "83ff96335c2d45a094df02a206a39ff4"),
        "ITEMS_PER_PAGE": scanners.get("items_per_page", 100),
        "JSON_OUT": os.path.join(root_dir, "output", "asx_placements.json")
    }

_CFG = load_config()
API_BASE = _CFG["API_BASE"]
PRICE_API = _CFG["PRICE_API"]
PDF_CDN = _CFG["PDF_CDN"]
PDF_TOKEN = _CFG["PDF_TOKEN"]
JSON_OUT = _CFG["JSON_OUT"]
ITEMS_PER_PAGE = _CFG["ITEMS_PER_PAGE"]

PLACEMENT_KEYWORDS = (
    "placement", "capital rais", "capital raise", "share purchase plan", "spp",
    "rights issue", "entitlement offer", "equity rais", "equity raise", "pro rata",
    "non-renounceable", "renounceable offer",
)
NOISE_TYPES = ("cleansing notice", "application for quotation", "appendix 2a", "change of director", "results of meeting", "notification of buy-back",)
REJECT_KEYWORDS = ("acquisition", "takeover", "merger", "exercise of options", "conversion", "dividend", "buy-back", "vesting", "lapse", "cancellation",)

# ── Helpers ──────────────────────────────────────────────────────────────────
def is_placement(headline: str, ann_types: List[str]) -> bool:
    hl = headline.lower()
    types_str = " ".join(ann_types).lower()
    if any(nt in types_str for nt in NOISE_TYPES): return False
    if any(rk in hl for rk in REJECT_KEYWORDS): return False
    if any(kw in hl for kw in PLACEMENT_KEYWORDS): return True
    if any(kw in types_str for kw in ("placement", "spp", "rights issue")): return True
    return False

def _clean_float(val: str) -> Optional[float]:
    try: return float(val.replace(",", "").replace("$", ""))
    except ValueError: return None

# ── PDF Extraction ───────────────────────────────────────────────────────────
def extract_price(text: str) -> Optional[float]:
    patterns = [
        r"(?:at|@)\s+(?:A?\$|NZ\$)\s*([\d,.]+)\s+per\s+(?:new\s+)?(?:share|security|ordinary)",
        r"(?:issue|offer|placement|subscription|purchase)\s+price[^\n$]{0,30}(?:A?\$|NZ\$)\s*([\d,.]+)",
        r"(?:price\s+of|price\s+per)\s*[^\n$]{0,25}(?:A?\$|NZ\$)\s*([\d,.]+)",
        r"(?:A?\$|NZ\$)\s*([\d,.]+)\s+per\s+share",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(1).rstrip(".")
            num = _clean_float(val)
            if num is not None and 0.005 < num <= 500.0: return num
    word_patterns = [(r"([\d,.]+)\s*cents?\s+per\s+share", 0.01), (r"([\d,.]+)\s*dollars?\s+per\s+share", 1.0)]
    for pat, multiplier in word_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(1).rstrip(".")
            num = _clean_float(val)
            if num is not None:
                final_val = num * multiplier
                if 0.005 < final_val <= 1000.0: return round(final_val, 6)
    return None

def extract_from_headline(headline: str) -> Dict[str, Optional[float]]:
    res: Dict[str, Optional[float]] = {"price": None}
    m3 = re.search(r"(?:at|@)\s*(?:A?\$|NZ\$)?\s*([\d,.]+)(?:c\b|\b)", headline, re.IGNORECASE)
    if m3:
        num = _clean_float(m3.group(1))
        if num is not None:
            end_pos = m3.end(1)
            if end_pos < len(headline) and headline[end_pos].lower() == "c": num = num / 100.0
            if 0.005 < num <= 500.0: res["price"] = num
    return res

def normalize_date(date_str: str) -> str:
    if not date_str: return ""
    try:
        if "/" in date_str:
            return datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
        return date_str
    except Exception: return date_str

def read_existing_yaml(yaml_path: str) -> Tuple[Optional[str], Set[str], List[Dict]]:
    existing_symbols: Set[str] = set()
    max_date: Optional[str] = None
    existing_rows: List[Dict] = []
    if not os.path.exists(yaml_path): return None, existing_symbols, existing_rows
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data: data = []
        for row in data:
            sym = str(row.get("ASX_Code", "")).strip()
            date = normalize_date(str(row.get("Date", "")).strip())
            if sym and date:
                existing_symbols.add(sym)
                if max_date is None or date > max_date: max_date = date
                existing_rows.append({
                    "symbol": sym, "company": str(row.get("Company", "")),
                    "headline": str(row.get("Headline", "")), "date": date,
                    "CR_Price": row.get("CR_Price", row.get("Price", "")),
                    "PDF_Link": str(row.get("PDF_Link", "")),
                })
    except Exception as e:
        print(f"Warning: Could not read existing YAML: {e}")
        return None, set(), []
    return max_date, existing_symbols, existing_rows

# ── Network & API ────────────────────────────────────────────────────────────
def fetch_announcements(months: int = 2, start_override: Optional[str] = None) -> List[Dict]:
    end_date = datetime.now()
    start_date = datetime.strptime(start_override, "%Y-%m-%d") if start_override else end_date - timedelta(days=months * 30)
    params = {"dateStart": start_date.strftime("%Y-%m-%d"), "dateEnd": end_date.strftime("%Y-%m-%d"), "announcementTypes[]": "issued capital", "itemsPerPage": ITEMS_PER_PAGE}
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    all_items: List[Dict] = []
    page = 0
    _info(f"Fetching ASX 'issued capital' announcements ({start_date:%Y-%m-%d} -> {end_date:%Y-%m-%d})...")
    while True:
        params["page"] = page
        try:
            r = session.get(API_BASE, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"  Error fetching page {page}: {e}")
            break
        items = data.get("data", {}).get("items", [])
        total = data.get("data", {}).get("count", 0)
        if not items: break
        all_items.extend(items)
        _dim(f"\r  Fetched {len(all_items)}/{total} announcements...")
        if len(all_items) >= total: break
        page += 1
        time.sleep(0.3)
    _info(f"\n  Total fetched: {len(all_items)}")
    return all_items

def sanitize_filename(name: str) -> str:
    valid_chars = "-_.() " + string.ascii_letters + string.digits
    return "".join(c for c in name if c in valid_chars).strip()[:80]

def download_pdf(doc_key: str, symbol: str, session: requests.Session, cache_dir: str, date: str, headline: str) -> Optional[bytes]:
    safe_hl = sanitize_filename(headline)
    cache_file = os.path.join(cache_dir, f"{date}_[{symbol}]_{safe_hl}.pdf")
    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            content = f.read()
            if content[:4] == b"%PDF": return content
    url = f"{PDF_CDN}{doc_key}?access_token={PDF_TOKEN}"
    try:
        r = session.get(url, timeout=30)
        if r.content[:4] != b"%PDF": return None
        with open(cache_file, "wb") as f: f.write(r.content)
        return r.content
    except: return None

def extract_pdf_text(pdf_bytes: bytes, max_pages: int = 5) -> str:
    if not PDF_SUPPORT or not pdf_bytes: return ""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            return "\n".join(p.extract_text() for p in pdf.pages[:max_pages] if p.extract_text())
    except: return ""

def process_event(event: Dict, session: requests.Session, cache_dir: str, skip_pdf: bool) -> Dict:
    price: Optional[float] = None
    if not skip_pdf:
        for doc_key in event["doc_keys"]:
            if price is not None: break
            pdf_bytes = download_pdf(doc_key, event["symbol"], session, cache_dir, event["date"], event["headline"])
            if pdf_bytes:
                text = extract_pdf_text(pdf_bytes)
                if text: price = extract_price(text)
    if price is None:
        hl_res = extract_from_headline(event["headline"])
        if hl_res["price"] is not None: price = hl_res["price"]
    event["CR_Price"] = price
    return event

def fetch_current_info(symbol: str, session: requests.Session) -> Tuple[str, Optional[float], str]:
    try:
        r = session.get(PRICE_API.format(symbol), timeout=10)
        data = r.json().get("data", {})
        return symbol, data.get("priceLast"), data.get("displayName", "")
    except: return symbol, None, ""

def fetch_liquidity_info(sym: str) -> Tuple[bool, str]:
    if not sym: return True, "No symbol"
    try:
        ticker = yf.Ticker(f"{sym}.AX")
        info = ticker.info
        if not info or 'regularMarketPrice' not in info:
            hist = ticker.history(period="10d")
            if hist.empty: return False, "No data/Delisted"
            mcap = info.get("marketCap", 0) if info else 0
            val = hist["Volume"].mean() * hist["Close"].iloc[-1]
            if mcap > 0 and mcap < 10_000_000: return False, f"MCap < 10M (${mcap:,.0f})"
            if val < 20_000: return False, f"Avg Daily Val < 20k (${val:,.0f})"
            return True, "OK"
        mcap, price = info.get("marketCap", 0), info.get("regularMarketPrice", info.get("currentPrice", info.get('previousClose', 0)))
        avg_vol = info.get("averageVolume", info.get("regularMarketVolume", 0))
        if not avg_vol or not price:
            hist = ticker.history(period="10d")
            if hist.empty: return False, "No trading data"
            avg_vol, price = hist["Volume"].mean(), hist["Close"].iloc[-1]
        if mcap > 0 and mcap < 10_000_000: return False, f"MCap < 10M (${mcap:,.0f})"
        if (avg_vol * price) < 20_000: return False, f"Avg Daily Val < 20k (${(avg_vol*price):,.0f})"
        return True, "OK"
    except Exception as e: return True, f"Checked but catch ({str(e)})"

# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="ASX Placement / Capital Raising Scanner")
    parser.add_argument("--months", type=int, default=2)
    parser.add_argument("--no-pdf", action="store_true")
    parser.add_argument("--full-refresh", action="store_true")
    args = parser.parse_args()

    root = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.abspath(os.path.join(root, "..", ".pdf_cache"))
    os.makedirs(cache_dir, exist_ok=True)
    config_dir = os.path.abspath(os.path.join(root, "..", "config"))
    os.makedirs(config_dir, exist_ok=True)
    yaml_db = os.path.join(config_dir, "asx_placements.yaml")

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    existing_symbols, start_override, existing_rows, fetch_new = set(), None, [], True
    if not args.full_refresh:
        max_date, existing_symbols, existing_rows = read_existing_yaml(yaml_db)
        if max_date:
            resume_date = datetime.strptime(max_date, "%Y-%m-%d") + timedelta(days=1)
            if resume_date <= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
                start_override = resume_date.strftime("%Y-%m-%d")
                print(f"Resuming from {start_override}")
            else: fetch_new = False

    raw_items = fetch_announcements(months=args.months, start_override=start_override) if fetch_new else []
    events: Dict[str, Dict] = {}
    for item in raw_items:
        sym, hl, ann_types = item.get("symbol", ""), item.get("headline", ""), item.get("announcementTypes", [])
        if not sym or not is_placement(hl, ann_types) or sym in existing_symbols: continue
        try:
            date_display = (datetime.fromisoformat(item.get("date", "").replace("Z", "+00:00")) + timedelta(hours=10)).strftime("%Y-%m-%d")
        except: date_display = item.get("date", "")[:10]
        event_key = f"{sym}_{date_display}"
        doc_key = item.get("documentKey", "")
        if event_key not in events:
            comp_info = item.get("companyInfo", [])
            events[event_key] = {"symbol": sym, "date": date_display, "company": comp_info[0].get("displayName", "") if comp_info else "", "headline": hl, "doc_keys": [doc_key] if doc_key else []}
        else:
            if doc_key and doc_key not in events[event_key]["doc_keys"]: events[event_key]["doc_keys"].append(doc_key)
            if hl and hl not in events[event_key]["headline"]: events[event_key]["headline"] += f" | {hl}"

    events_list = list(events.values())
    processed_events = []
    if events_list:
        _info(f"Processing {len(events_list)} new events...")
        with ThreadPoolExecutor(max_workers=min(20, len(events_list))) as ex:
            processed_events = list(ex.map(lambda ev: process_event(ev, session, cache_dir, args.no_pdf), events_list))
        
        _info(f"Filtering liquidity for {len(processed_events)} new events...")
        final_processed = []
        with ThreadPoolExecutor(max_workers=min(20, len(processed_events))) as ex:
            results = ex.map(lambda ev: (ev, fetch_liquidity_info(ev["symbol"])), processed_events)
            for ev, (is_liquid, reason) in results:
                if is_liquid: final_processed.append(ev)
                else: _warn(f"  Removed {ev['symbol']}: {reason}")
        processed_events = final_processed

    final_events_map = {ev["symbol"]: ev for ev in (existing_rows + processed_events)}
    all_events = list(final_events_map.values())
    if not all_events: return

    unique_symbols = [ev["symbol"] for ev in all_events]
    _info(f"Fetching live prices for {len(unique_symbols)} symbols...")
    price_map, name_map = {}, {}
    with ThreadPoolExecutor(max_workers=20) as ex:
        for sym, px, dname in ex.map(lambda s: fetch_current_info(s, session), unique_symbols):
            if px is not None: price_map[sym] = px
            if dname: name_map[sym] = dname
    
    yaml_data = []
    for ev in all_events:
        sym, cur_px = ev["symbol"], price_map.get(ev["symbol"])
        cp = ev.get("CR_Price")
        if isinstance(cp, str) and cp.strip():
            try: cp = float(cp.replace(",", "").replace("$", ""))
            except: pass
        
        diff = None
        if cur_px is not None and isinstance(cp, (int, float)) and cp > 0:
            diff = round(((cur_px - cp) / cp) * 100, 2)

        yaml_data.append({
            "ASX_Code": sym, "Company": ev.get("company") or name_map.get(sym, ""),
            "Headline": ev.get("headline", ""), "Date": ev.get("date", ""),
            "CR_Price": cp if cp not in (None, "") else "", "Current_Price": cur_px if cur_px is not None else "",
            "Price_Diff_%": diff if diff is not None else "",
            "PDF_Link": ev.get("PDF_Link") or (f"{PDF_CDN}{ev['doc_keys'][0]}?access_token={PDF_TOKEN}" if ev.get("doc_keys") else "")
        })

    with open(yaml_db, "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump({'placements': yaml_data, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, f, indent=2, ensure_ascii=False)
    
    _ok(f"Headless Sync: Exported {len(yaml_data)} placements to {JSON_OUT}")

if __name__ == "__main__":
    main()
