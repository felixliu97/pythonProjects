"""
ASX Price Sensitive Announcements Scanner

Scans ASX announcements for strictly price-sensitive events (utilizing API filters),
downloads PDFs, extracts summaries, and outputs to YAML and JSON.
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
import yaml
import requests
import json

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("Warning: pdfplumber not installed. PDF analysis disabled.")

class _C:
    R=chr(27)+'[0m'; DIM=chr(27)+'[2m'; GREEN=chr(27)+'[92m'
    YELLOW=chr(27)+'[93m'; BOLD=chr(27)+'[1m'
def _ok(m):   print(f"{_C.GREEN}{m}{_C.R}")
def _warn(m): print(f"{_C.YELLOW}{m}{_C.R}")
def _dim(m):  print(f"{_C.DIM}{m}{_C.R}",  end="", flush=True)
def _info(m): print(f"{_C.DIM}{m}{_C.R}")

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
        "HEADER_API": api.get("company_header", "https://asx.api.markitdigital.com/asx-research/1.0/companies/{}/header"),
        "PDF_CDN": api.get("pdf_cdn", "https://cdn-api.markitdigital.com/apiman-gateway/ASX/asx-research/1.0/file/"),
        "PDF_TOKEN": api.get("pdf_token", "83ff96335c2d45a094df02a206a39ff4"),
        "ITEMS_PER_PAGE": scanners.get("items_per_page", 100),
        "JSON_OUT": os.path.join(root_dir, "output", "asx_announcements.json")
    }

_CFG = load_config()
API_BASE = _CFG["API_BASE"]
HEADER_API = _CFG["HEADER_API"]
PDF_CDN = _CFG["PDF_CDN"]
PDF_TOKEN = _CFG["PDF_TOKEN"]
JSON_OUT = _CFG["JSON_OUT"]
ITEMS_PER_PAGE = _CFG["ITEMS_PER_PAGE"]

NOISE_KEYWORDS = (
    "trading halt", "pausing in trading", "pause in trading", 
    "response to asx", "price query", "notification of buy-back",
    "suspension from quotation", "cleansing notice", "market update",
    "on-market share buyback", "on-market buy-back", "investor presentation",
    "disclosure document", "dividend/distribution", "investor webinar presentation"
)

def normalize_date(date_str: str) -> str:
    if not date_str: return ""
    try:
        if "/" in date_str:
            return datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
        return date_str
    except Exception:
        return date_str

def read_existing_yaml(yaml_path: str) -> Tuple[Optional[str], Set[str], List[Dict]]:
    existing_keys = set()
    max_date = None
    existing_anns = []

    if not os.path.exists(yaml_path):
        return None, existing_keys, existing_anns

    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        if not data:
            data = []
            
        for row in data:
            sym = str(row.get("ASX_Code", "")).strip()
            raw_date = str(row.get("Date", "")).strip()
            date = normalize_date(raw_date)
            headline = str(row.get("Headline", "")).strip()
            
            if sym and date:
                key = f"{sym}_{date}_{headline[:50]}"
                existing_keys.add(key)
                if max_date is None or date > max_date:
                    max_date = date
                existing_anns.append({
                    "ASX_Code": sym,
                    "Company": str(row.get("Company", "")),
                    "Headline": headline,
                    "Date": date,
                    "Summary": str(row.get("Summary", "")),
                    "PDF_Link": str(row.get("PDF_Link", "")),
                    "Rating": int(row.get("Rating", 2))
                })
    except Exception as e:
        print(f"Warning: Could not read existing YAML: {e}")
        return None, set(), []

    return max_date, existing_keys, existing_anns

def fetch_announcements(months: int = 2, start_override: Optional[str] = None) -> List[Dict]:
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
    _info(f"Fetching ASX price-sensitive announcements ({start_date:%Y-%m-%d} -> {end_date:%Y-%m-%d})...")

    while True:
        params["page"] = page
        try:
            r = session.get(API_BASE, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
        except:
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

def fetch_company_name(symbol: str, session: requests.Session) -> Tuple[str, str]:
    try:
        url = HEADER_API.format(symbol)
        r = session.get(url, timeout=10)
        data = r.json().get("data", {})
        return symbol, data.get("displayName", "")
    except:
        return symbol, ""

def sanitize_filename(name: str) -> str:
    valid_chars = "-_.() " + string.ascii_letters + string.digits
    cleaned = ''.join(c for c in name if c in valid_chars)
    return cleaned.strip()[:80]

def download_pdf(doc_key: str, session: requests.Session) -> Optional[bytes]:
    url = f"{PDF_CDN}{doc_key}?access_token={PDF_TOKEN}"
    try:
        r = session.get(url, timeout=30)
        if r.content[:4] == b"%PDF":
            return r.content
    except:
        pass
    return None

def extract_pdf_summary(pdf_bytes: bytes, max_pages: int = 5) -> str:
    if not PDF_SUPPORT or not pdf_bytes: return ""
    parts = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages[:max_pages]:
                pt = page.extract_text()
                if pt: parts.append(pt)
        text = "\n".join(parts)
        return _parse_summary(text)
    except:
        return ""

def _parse_summary(text: str) -> str:
    if not text: return ""
    lines = text.split("\n")
    body_lines = []
    skip_patterns = re.compile(
        r"^(?:asx\s*(?:announcement|release)|page\s+\d|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|"
        r"(?:abn|acn|arbn)|for\s+immediate|media\s+release|not\s+for\s+distribution|www\.|level\s+\d|suite\s+\d|"
        r"\d+\s+\w+\s+street|tel[:\s]|fax[:\s]|phone[:\s]|e[\s-]*mail|po\s+box)",
        re.IGNORECASE
    )
    for line in lines:
        stripped = line.strip()
        if len(stripped) < 15 or skip_patterns.search(stripped): continue
        if stripped == stripped.upper() and len(stripped) < 80: continue
        body_lines.append(stripped)
        if len(body_lines) >= 6: break
    if not body_lines: return ""
    body_text = " ".join(body_lines)
    sentences = re.split(r"(?<=[.!?])\s+", body_text)
    summary = ""
    for s in sentences:
        if len(summary) + len(s) > 300: break
        summary = (summary + " " + s).strip()
    return summary if summary else body_text[:300]

def calculate_rating(headline: str, summary: str) -> int:
    hl = headline.lower()
    if any(kw in hl for kw in ["discovery", "high-grade", "high grade", "bonanza", "spectacular", "exceptional", "tier 1", "world class", "maiden resource", "production commenced", "etf", "inclusion", "index", "msci", "s&p", "streaming", "offtake", "fortune 500", "patent granted", "white house", "fast-41"]):
        return 5
    is_billion = any(kw in hl for kw in ["billion", "bn", " b ", "b$"])
    has_large_money = is_billion or (any(kw in hl for kw in ["$", "million", " m ", "m$"]) and any(f"{i}00" in hl for i in range(1, 10)))
    if has_large_money:
        if any(kw in hl for kw in ["commitment", "offer", "strategic", "agreement", "financing", "funding", "hybrid", "securities", "launch", "collaboration"]):
            return 5
        return 4
    if any(kw in hl for kw in ["resource upgrade", "binding offtake", "major acquisition", "dfs", "pfs", "feasibility", "final investment decision", "fid", "takeover", "merger", "award", "contract", "financing", "funding", "facility", "agreement", "strategic"]):
        return 4
    if any(kw in hl for kw in ["high-grade", "high grade"]) and any(kw in hl for kw in ["assay", "results", "drilling"]):
        return 4
    if any(kw in hl for kw in ["assay", "results", "drilling", "commenced", "strategic partnership", "mou", "capital raise", "placement", "acquisition"]):
        return 3
    if any(kw in (summary.lower() if summary else "") for kw in ["high-grade", "high grade", "discovery"]):
        return 3
    if any(kw in hl for kw in ["termination", "withdrawal", "disappointing", "delay", "failed", "cancelled"]):
        return 1
    return 2

def process_event(event: Dict, session: requests.Session, pdf_dir: str, skip_pdf: bool) -> Dict:
    summary = ""
    if not skip_pdf:
        for doc_key in event.get("doc_keys", []):
            safe_hl = sanitize_filename(event['headline'])
            pdf_filename = f"{event['date']}_[{event['symbol']}]_{safe_hl}.pdf"
            pdf_path = os.path.join(pdf_dir, pdf_filename)
            pdf_bytes = None
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    content = f.read()
                    if content[:4] == b"%PDF": pdf_bytes = content
            if not pdf_bytes:
                pdf_bytes = download_pdf(doc_key, session)
                if pdf_bytes:
                    with open(pdf_path, "wb") as f: f.write(pdf_bytes)
            if pdf_bytes:
                summary = extract_pdf_summary(pdf_bytes)
                if summary: break
    event["Summary"] = summary if summary else event["headline"]
    event["Rating"] = calculate_rating(event["headline"], event["Summary"])
    return event

def main() -> None:
    parser = argparse.ArgumentParser(description="ASX Price Sensitive Announcements Scanner")
    parser.add_argument("--months", type=int, default=2, help="Lookback months (default: 2)")
    parser.add_argument("--no-pdf", action="store_true", help="Skip PDF download & extraction")
    parser.add_argument("--full-refresh", action="store_true", help="Ignore existing database; full re-scan")
    args = parser.parse_args()

    root = os.path.dirname(os.path.abspath(__file__))
    pdf_dir = os.path.abspath(os.path.join(root, "..", ".pdf_cache"))
    os.makedirs(pdf_dir, exist_ok=True)
    config_dir = os.path.abspath(os.path.join(root, "..", "config"))
    os.makedirs(config_dir, exist_ok=True)
    yaml_db = os.path.join(config_dir, "asx_announcements.yaml")

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    existing_keys = set()
    start_override = None
    existing_anns = []

    if not args.full_refresh:
        max_date, existing_keys, existing_anns = read_existing_yaml(yaml_db)
        if max_date:
            start_override = max_date
            _info(f"Checking for new announcements starting from {max_date}...")
        else:
            _info("No existing database found.")
    
    raw_items = fetch_announcements(args.months, start_override)
    events_map = {}
    for item in raw_items:
        hl = item.get("headline", "")
        if any(nk in hl.lower() for nk in NOISE_KEYWORDS): continue
        sym = item.get("symbol", "")
        if not sym: continue
        date_str = item.get("date", "")
        try:
            utc_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            date_display = (utc_dt + timedelta(hours=10)).strftime("%Y-%m-%d")
        except:
            date_display = date_str[:10] if date_str else ""

        dedup_key = f"{sym}_{date_display}_{hl[:50]}"
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
    processed_events = []
    if events_list:
        _info(f"Processing {len(events_list)} new announcements...")
        workers = min(10, max(1, len(events_list)))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(process_event, ev, session, pdf_dir, args.no_pdf): ev for ev in events_list}
            for future in as_completed(futures):
                processed_events.append(future.result())
        print()

    new_anns_mapped = []
    for ev in processed_events:
        pdf_link = f"{PDF_CDN}{ev['doc_keys'][0]}?access_token={PDF_TOKEN}" if ev.get("doc_keys") else ""
        new_anns_mapped.append({
            "ASX_Code": ev["symbol"], "Company": "", 
            "Headline": ev.get("headline", ""), "Date": ev.get("date", ""),
            "Summary": ev.get("Summary", ""), "PDF_Link": pdf_link,
            "Rating": ev.get("Rating", 2)
        })

    all_announcements = existing_anns + new_anns_mapped
    if not all_announcements:
        print("No data.")
        return

    symbols_to_fetch = list({ann["ASX_Code"] for ann in all_announcements if not ann.get("Company")})
    if symbols_to_fetch:
        _info(f"Fetching names for {len(symbols_to_fetch)} symbols...")
        name_map = {}
        with ThreadPoolExecutor(max_workers=20) as executor:
            for sym, dname in executor.map(lambda s: fetch_company_name(s, session), symbols_to_fetch):
                if dname: name_map[sym] = dname
        for ann in all_announcements:
            if ann["ASX_Code"] in name_map: ann["Company"] = name_map[ann["ASX_Code"]]

    all_announcements.sort(key=lambda x: (x.get("Date", ""), x.get("Rating", 2)), reverse=True)
    one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    all_announcements = [ann for ann in all_announcements if ann.get("Date", "") >= one_week_ago]
    
    with open(yaml_db, "w", encoding="utf-8") as f:
        yaml.dump(all_announcements, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump({'announcements': all_announcements, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, f, indent=2, ensure_ascii=False)
    
    _ok(f"Headless Sync: Exported {len(all_announcements)} valid announcements to {JSON_OUT}")

if __name__ == "__main__":
    main()
