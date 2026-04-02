"""
ASX Placement / Capital Raising Scanner

Scans ASX announcements for capital raising events, deduplicates by symbol
and date, extracts financial details from PDFs (multi-threaded), fetches
real-time prices, and outputs to YAML and HTML.

Supports incremental mode: reads existing database to resume from max_date.
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

try:
    import pdfplumber

    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


# ── Constants ────────────────────────────────────────────────────────────────

API_BASE = (
    "https://asx.api.markitdigital.com/asx-research/1.0"
    "/markets/announcements"
)
PRICE_API = (
    "https://asx.api.markitdigital.com/asx-research/1.0"
    "/companies/{}/header"
)
PDF_CDN = (
    "https://cdn-api.markitdigital.com/apiman-gateway"
    "/ASX/asx-research/1.0/file/"
)
PDF_TOKEN = "83ff96335c2d45a094df02a206a39ff4"
ITEMS_PER_PAGE = 100

PLACEMENT_KEYWORDS = (
    "placement",
    "capital rais",
    "capital raise",
    "share purchase plan",
    "spp",
    "rights issue",
    "entitlement offer",
    "equity rais",
    "equity raise",
    "pro rata",
    "non-renounceable",
    "renounceable offer",
)

NOISE_TYPES = (
    "cleansing notice",
    "application for quotation",
    "appendix 2a",
    "change of director",
    "results of meeting",
    "notification of buy-back",
)

REJECT_KEYWORDS = (
    "acquisition",
    "takeover",
    "merger",
    "exercise of options",
    "conversion",
    "dividend",
    "buy-back",
    "vesting",
    "lapse",
    "cancellation",
)




# ── Helpers ──────────────────────────────────────────────────────────────────


def is_placement(headline: str, ann_types: List[str]) -> bool:
    """Return True if the announcement looks like a capital raising event."""
    hl = headline.lower()
    types_str = " ".join(ann_types).lower()

    # Reject if any noise type matches
    if any(nt in types_str for nt in NOISE_TYPES):
        return False

    # Reject if any reject keyword matches in headline
    if any(rk in hl for rk in REJECT_KEYWORDS):
        return False

    # Direct keyword match in headline
    if any(kw in hl for kw in PLACEMENT_KEYWORDS):
        return True

    # Check announcement types
    if any(kw in types_str for kw in ("placement", "spp", "rights issue")):
        return True

    return False


def _clean_float(val: str) -> Optional[float]:
    """Strip $ and commas, return a float or None."""
    try:
        return float(val.replace(",", "").replace("$", ""))
    except ValueError:
        return None


# ── PDF Extraction ───────────────────────────────────────────────────────────
def extract_price(text: str) -> Optional[float]:
    """Extract placement price-per-share from PDF text.

    Supports:
    - $X.XX
    - X cents per share
    - X dollars per share

    Returns a raw float or None.
    """
    # 1. Standard price patterns (@ $0.05, issue price $0.05)
    patterns = [
        r"(?:at|@)\s+(?:A?\$|NZ\$)\s*([\d,.]+)\s+per\s+"
        r"(?:new\s+)?(?:share|security|ordinary)",
        r"(?:issue|offer|placement|subscription|purchase)\s+price"
        r"[^\n$]{0,30}(?:A?\$|NZ\$)\s*([\d,.]+)",
        r"(?:price\s+of|price\s+per)\s*[^\n$]{0,25}"
        r"(?:A?\$|NZ\$)\s*([\d,.]+)",
        r"(?:A?\$|NZ\$)\s*([\d,.]+)\s+per\s+share",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(1).rstrip(".")
            num = _clean_float(val)
            if num is not None and 0.005 < num <= 500.0:
                return num

    # 2. Cents/Dollars phrasing (e.g., "5 cents per share", "1 dollar per share")
    # Matches: 1.25 cents, 5 cents, 0.5 cent, 1 dollar, 2 dollars
    word_patterns = [
        (r"([\d,.]+)\s*cents?\s+per\s+share", 0.01),
        (r"([\d,.]+)\s*dollars?\s+per\s+share", 1.0),
    ]
    for pat, multiplier in word_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(1).rstrip(".")
            num = _clean_float(val)
            if num is not None:
                final_val = num * multiplier
                if 0.005 < final_val <= 1000.0:
                    return round(final_val, 6)

    return None


def extract_from_headline(
    headline: str,
) -> Dict[str, Optional[float]]:
    """Fallback extraction from headline text.

    Returns dict with 'price' as raw float or None.
    """
    res: Dict[str, Optional[float]] = {"price": None}

    # Price from headline (e.g. "@ 2.5c" or "@ $0.02")
    m3 = re.search(
        r"(?:at|@)\s*(?:A?\$|NZ\$)?\s*([\d,.]+)(?:c\b|\b)",
        headline,
        re.IGNORECASE,
    )
    if m3:
        num = _clean_float(m3.group(1))
        if num is not None:
            end_pos = m3.end(1)
            if (
                end_pos < len(headline)
                and headline[end_pos].lower() == "c"
            ):
                num = num / 100.0
            if 0.005 < num <= 500.0:
                res["price"] = num

    return res


def normalize_date(date_str: str) -> str:
    """Normalize date string to YYYY-MM-DD, handling Excel's M/D/YYYY formats."""
    if not date_str:
        return ""
    try:
        if "/" in date_str:
            dt = datetime.strptime(date_str, "%m/%d/%Y")
            return dt.strftime("%Y-%m-%d")
        # Assume already YYYY-MM-DD
        return date_str
    except Exception:
        return date_str


def read_existing_yaml(
    yaml_path: str,
) -> Tuple[Optional[str], Set[str], List[Dict]]:
    """Read existing YAML and return (max_date, set of 'SYMBOL' keys, existing_rows)."""
    existing_symbols: Set[str] = set()
    max_date: Optional[str] = None
    existing_rows: List[Dict] = []

    if not os.path.exists(yaml_path):
        return None, existing_symbols, existing_rows

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            data = []
            
        for row in data:
            sym = str(row.get("ASX_Code", "")).strip()
            raw_date = str(row.get("Date", "")).strip()
            date = normalize_date(raw_date)
            if sym and date:
                existing_symbols.add(sym)
                if max_date is None or date > max_date:
                    max_date = date
                
                norm_row = {
                    "symbol": sym,
                    "company": str(row.get("Company", "")),
                    "headline": str(row.get("Headline", "")),
                    "date": date,
                    "CR_Price": row.get("CR_Price", row.get("Price", "")),
                    "PDF_Link": str(row.get("PDF_Link", "")),
                }
                existing_rows.append(norm_row)
    except Exception as e:
        print(f"Warning: Could not read existing YAML: {e}")
        return None, set(), []

    return max_date, existing_symbols, existing_rows


# ── Network & API ────────────────────────────────────────────────────────────


def fetch_announcements(
    months: int = 2,
    start_override: Optional[str] = None,
) -> List[Dict]:
    """Fetch 'issued capital' announcements from the ASX API."""
    end_date = datetime.now()
    if start_override:
        start_date = datetime.strptime(start_override, "%Y-%m-%d")
    else:
        start_date = end_date - timedelta(days=months * 30)

    params = {
        "dateStart": start_date.strftime("%Y-%m-%d"),
        "dateEnd": end_date.strftime("%Y-%m-%d"),
        "announcementTypes[]": "issued capital",
        "itemsPerPage": ITEMS_PER_PAGE,
    }

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36"
            ),
            "Accept": "application/json",
        }
    )

    all_items: List[Dict] = []
    page = 0
    print(
        f"Fetching ASX 'issued capital' announcements "
        f"({start_date:%Y-%m-%d} -> {end_date:%Y-%m-%d})..."
    )

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

        if not items:
            break

        all_items.extend(items)
        print(
            f"\r  Fetched {len(all_items)}/{total} announcements...",
            end="",
            flush=True,
        )

        if len(all_items) >= total:
            break

        page += 1
        time.sleep(0.3)

    print(f"\n  Total fetched: {len(all_items)}")
    return all_items


def sanitize_filename(name: str) -> str:
    valid_chars = "-_.() " + string.ascii_letters + string.digits
    cleaned = ''.join(c for c in name if c in valid_chars)
    return cleaned.strip()[:80]


def download_pdf(
    doc_key: str,
    symbol: str,
    session: requests.Session,
    cache_dir: str,
    date: str,
    headline: str,
) -> Optional[bytes]:
    """Download a PDF or serve it from the local cache."""
    safe_hl = sanitize_filename(headline)
    pdf_filename = f"{date}_[{symbol}]_{safe_hl}.pdf"
    cache_file = os.path.join(cache_dir, pdf_filename)

    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            content = f.read()
        if content[:4] == b"%PDF":
            return content

    url = f"{PDF_CDN}{doc_key}?access_token={PDF_TOKEN}"
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
        if r.content[:4] != b"%PDF":
            return None
        with open(cache_file, "wb") as f:
            f.write(r.content)
        return r.content
    except Exception:
        return None


def extract_pdf_text(
    pdf_bytes: bytes, max_pages: int = 5
) -> str:
    """Extract text from the first N pages of a PDF."""
    if not PDF_SUPPORT or not pdf_bytes:
        return ""
    parts: List[str] = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages[:max_pages]:
                page_text = page.extract_text()
                if page_text:
                    parts.append(page_text)
        return "\n".join(parts)
    except Exception:
        return ""


def process_event(
    event: Dict,
    session: requests.Session,
    cache_dir: str,
    skip_pdf: bool,
) -> Dict:
    """Process a single deduplicated (symbol, date) event.

    Populates CR_Price as raw numeric.
    """
    price: Optional[float] = None

    # 1. Try PDF extraction across all documents
    if not skip_pdf:
        for doc_key in event["doc_keys"]:
            if price is not None:
                break

            pdf_bytes = download_pdf(
                doc_key, event["symbol"], session, cache_dir, event["date"], event["headline"]
            )
            if pdf_bytes:
                text = extract_pdf_text(pdf_bytes)
                if text:
                    if price is None:
                        price = extract_price(text)

    # 2. Headline fallback
    if price is None:
        hl_res = extract_from_headline(event["headline"])
        if hl_res["price"] is not None:
            price = hl_res["price"]

    event["CR_Price"] = price
    return event


def fetch_current_info(
    symbol: str, session: requests.Session
) -> Tuple[str, Optional[float], str]:
    """Fetch the live price and company name for a single symbol."""
    try:
        url = PRICE_API.format(symbol)
        r = session.get(url, timeout=10)
        data = r.json().get("data", {})
        return symbol, data.get("priceLast"), data.get("displayName", "")
    except Exception:
        return symbol, None, ""


def fetch_liquidity_info(sym: str) -> Tuple[bool, str]:
    """Check if stock meets minimum liquidity requirements (MCap >= 10M, Daily Val >= 20k)."""
    if not sym:
        return True, "No symbol"
    try:
        ticker = yf.Ticker(f"{sym}.AX")
        info = ticker.info
        
        # Sometime yfinance returns empty info for delisted/suspended stocks
        if not info or 'regularMarketPrice' not in info:
            # Let's try to get history as fallback to check if it's trading
            hist = ticker.history(period="10d")
            if hist.empty:
                return False, "No data/Delisted"
            # Estimate from history
            mcap = info.get("marketCap", 0) if info else 0
            avg_vol = hist["Volume"].mean()
            price = hist["Close"].iloc[-1]
            val = avg_vol * price
            
            if mcap > 0 and mcap < 10_000_000:
                return False, f"MCap < 10M (${mcap:,.0f})"
            if val < 20_000:
                return False, f"Avg Daily Val < 20k (${val:,.0f})"
            return True, "OK"
            
        mcap = info.get("marketCap", 0)
        avg_vol = info.get("averageVolume", info.get("regularMarketVolume", 0))
        price = info.get("regularMarketPrice", info.get("currentPrice", 0))
        
        if not price and 'previousClose' in info:
            price = info['previousClose']
            
        # fallback to history if info is incomplete
        if not avg_vol or not price:
            hist = ticker.history(period="10d")
            if hist.empty:
                return False, "No trading data"
            avg_vol = hist["Volume"].mean()
            price = hist["Close"].iloc[-1]
            
        daily_val = avg_vol * price
        
        if mcap > 0 and mcap < 10_000_000:
            return False, f"MCap < 10M (${mcap:,.0f})"
        
        if daily_val < 20_000:
            return False, f"Avg Daily Val < 20k (${daily_val:,.0f})"
            
        return True, "OK"
        
    except Exception as e:
        return True, f"Error, kept for safety ({str(e)})"


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ASX Placement / Capital Raising Scanner"
    )
    parser.add_argument(
        "--months",
        type=int,
        default=2,
        help="Lookback months (used only on first run or --full-refresh)",
    )
    parser.add_argument(
        "--no-pdf",
        action="store_true",
        help="Skip PDF download & extraction",
    )
    parser.add_argument(
        "--full-refresh",
        action="store_true",
        help="Ignore existing database; full re-scan and overwrite",
    )
    parser.add_argument(
        "--html-only",
        action="store_true",
        help="Only generate HTML from existing YAML (no API calls)",
    )
    args = parser.parse_args()

    if args.html_only:
        print("\n=== Generating Placements HTML from YAML ===")
        generate_html()
        return

    root = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.abspath(os.path.join(root, "..", ".pdf_cache"))
    os.makedirs(cache_dir, exist_ok=True)
    out_dir = os.path.abspath(os.path.join(root, "..", "output"))
    os.makedirs(out_dir, exist_ok=True)
    config_dir = os.path.abspath(os.path.join(root, "..", "config"))
    os.makedirs(config_dir, exist_ok=True)
    
    yaml_db = os.path.join(config_dir, "asx_placements.yaml")

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36"
            ),
        }
    )

    # ── 0. Determine scan range from existing YAML ────────────────────────
    existing_symbols: Set[str] = set()
    start_override: Optional[str] = None
    existing_rows: List[Dict] = []
    fetch_new = True

    if not args.full_refresh:
        max_date, existing_symbols, existing_rows = read_existing_yaml(yaml_db)
        if max_date:
            resume_date = (
                datetime.strptime(max_date, "%Y-%m-%d")
                + timedelta(days=1)
            )
            today = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            if resume_date <= today:
                start_override = resume_date.strftime("%Y-%m-%d")
                print(
                    f"Resuming from {start_override} "
                    f"(existing database max date: {max_date})"
                )
            else:
                print(
                    f"Database is already up to date "
                    f"(max date: {max_date}). Updating latest prices for existing records."
                )
                fetch_new = False

    # ── 1. Fetch announcements ───────────────────────────────────────────
    raw_items = []
    if fetch_new:
        raw_items = fetch_announcements(
            months=args.months, start_override=start_override
        )

    # ── 2. Filter & deduplicate by (Symbol, Date) ────────────────────────
    events: Dict[str, Dict] = {}

    for item in raw_items:
        hl = item.get("headline", "")
        ann_types = item.get("announcementTypes", [])

        if not is_placement(hl, ann_types):
            continue

        sym = item.get("symbol", "")
        if not sym:
            continue

        date_str = item.get("date", "")
        try:
            utc_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            syd_dt = utc_dt + timedelta(hours=10)
            date_display = syd_dt.strftime("%Y-%m-%d")
        except Exception:
            date_display = date_str[:10] if date_str else ""

        event_key = f"{sym}_{date_display}"

        # Skip if the symbol already exists in our master YAML
        if sym in existing_symbols:
            continue

        doc_key = item.get("documentKey", "")

        if event_key not in events:
            comp_info = item.get("companyInfo", [])
            comp_info = comp_info[0] if comp_info else {}
            events[event_key] = {
                "symbol": sym,
                "date": date_display,
                "company": comp_info.get("displayName", ""),
                "headline": hl,
                "doc_keys": [doc_key] if doc_key else [],
            }
        else:
            if (
                doc_key
                and doc_key not in events[event_key]["doc_keys"]
            ):
                events[event_key]["doc_keys"].append(doc_key)
            if hl and hl not in events[event_key]["headline"]:
                events[event_key]["headline"] += f" | {hl}"

    events_list = list(events.values())
    if events_list:
        print(
            f"\nFiltered and deduplicated to "
            f"{len(events_list)} new placement events."
        )
    else:
        print("\nNo new placements found to fetch.")

    # ── 3. Parallel PDF extraction ───────────────────────────────────────
    total = len(events_list)
    completed = 0
    processed_events: List[Dict] = []
    
    if total > 0:
        print(
            f"Processing PDFs & extracting data "
            f"(Total events: {total})..."
        )

        workers = min(20, max(1, total))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    process_event, ev, session, cache_dir, args.no_pdf
                ): ev
                for ev in events_list
            }
            for future in as_completed(futures):
                processed_events.append(future.result())
                completed += 1
                print(
                    f"\r  Processed {completed}/{total} events",
                    end="",
                    flush=True,
                )
        print()
        
    # ── 3.6 Filter liquidity for NEW events using yfinance ───────────────
    if processed_events:
        unique_new_symbols = list({ev["symbol"] for ev in processed_events})
        print(f"\nFiltering liquidity for {len(unique_new_symbols)} new symbols...")
        symbol_status = {}
        
        workers = min(20, max(1, len(unique_new_symbols)))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(fetch_liquidity_info, sym): sym for sym in unique_new_symbols}
            done = 0
            for future in as_completed(futures):
                sym = futures[future]
                is_liquid, reason = future.result()
                symbol_status[sym] = (is_liquid, reason)
                done += 1
                if done % 10 == 0:
                    print(f"\r  Processed {done}/{len(unique_new_symbols)} liquidity checks...", end="", flush=True)
        print()
                    
        removed = []
        filtered_new_events = []
        for ev in processed_events:
            sym = ev["symbol"]
            is_liquid, reason = symbol_status.get(sym, (True, "Unchecked"))
            if is_liquid:
                filtered_new_events.append(ev)
            else:
                removed.append((sym, reason))
                
        unique_removed = list(set(removed))
        unique_removed.sort()
        
        if unique_removed:
            print(f"\n--- Removed {len(unique_removed)} illiquid new symbols ---")
            for sym, reason in unique_removed:
                 print(f"  {sym}: {reason}")
                 
        processed_events = filtered_new_events

    # ── 3.5 Strict Deduplication: One row per stock (Preserve Original) ──
    final_events_map: Dict[str, Dict] = {}
    for ev in (existing_rows + processed_events):
        sym = ev["symbol"]
        if sym not in final_events_map:
            final_events_map[sym] = ev
    
    all_events = list(final_events_map.values())

    if not all_events:
        print("No events to process.")
        return

    # ── 4. Fetch current prices concurrently ─────────────────────────────
    unique_symbols = list(
        {ev["symbol"] for ev in all_events}
    )
    print(
        f"Fetching live prices for "
        f"{len(unique_symbols)} symbols..."
    )

    price_map: Dict[str, float] = {}
    name_map: Dict[str, str] = {}
    workers = min(20, max(1, len(unique_symbols)))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                fetch_current_info, sym, session
            ): sym
            for sym in unique_symbols
        }
        for future in as_completed(futures):
            sym, px, dname = future.result()
            if px is not None:
                price_map[sym] = px
            if dname:
                name_map[sym] = dname
    print(
        f"  Got price/info for {len(price_map)}/"
        f"{len(unique_symbols)} symbols."
    )

    # ── 5. Build final rows (all numerics raw) ───────────────────────────
    rows: List[Dict] = []
    for ev in all_events:
        sym = ev["symbol"]
        cur_price = price_map.get(sym)
        
        comp_name = ev.get("company", "")
        if not comp_name:
            comp_name = name_map.get(sym, "")

        # Price diff calculation
        diff: Optional[float] = None
        placement_price_raw = ev.get("CR_Price")
        placement_price = None
        if placement_price_raw not in (None, ""):
            try:
                placement_price = float(str(placement_price_raw).replace(",", "").replace("$", ""))
            except ValueError:
                pass

        if cur_price is not None and placement_price is not None:
            if placement_price > 0:
                diff = round(
                    ((cur_price - placement_price) / placement_price)
                    * 100,
                    2,
                )

        # PDF link
        pdf_link = ev.get("PDF_Link", "")
        if not pdf_link and ev.get("doc_keys"):
            pdf_link = (
                f"{PDF_CDN}{ev['doc_keys'][0]}"
                f"?access_token={PDF_TOKEN}"
            )

        rows.append(
            {
                "ASX_Code": sym,
                "Company": comp_name,
                "Headline": ev.get("headline", ""),
                "Date": ev.get("date", ""),
                "CR_Price": ev.get("CR_Price") if ev.get("CR_Price") not in (None, "") else "",
                "Current_Price": cur_price if cur_price is not None else "",
                "Price_Diff_%": diff if diff is not None else "",
                "PDF_Link": pdf_link,
            }
        )

    print(f"\nProcessed {len(rows)} valid placement events.")

    # ── Export YAML config ───────────────────────────────────────────────
    config_dir = os.path.abspath(os.path.join(root, "..", "config"))
    os.makedirs(config_dir, exist_ok=True)
    yaml_path = os.path.join(config_dir, "asx_placements.yaml")
    yaml_data = []
    for r in rows:
        cr_p = r.get("CR_Price", "")
        # Ensure CR_Price is numeric if possible
        if isinstance(cr_p, str) and cr_p.strip():
            try:
                cr_p = float(cr_p.replace(",", "").replace("$", ""))
            except ValueError:
                pass
        
        yaml_data.append({
            "ASX_Code": r["ASX_Code"],
            "Company": r.get("Company", ""),
            "Headline": r.get("Headline", ""),
            "Date": r.get("Date", ""),
            "CR_Price": cr_p,
            "Current_Price": r.get("Current_Price", ""),
            "Price_Diff_%": r.get("Price_Diff_%", ""),
            "PDF_Link": r.get("PDF_Link", ""),
        })
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print(f"Exported YAML config to {yaml_path}")

    print("\n=== Generating Placements HTML ===")
    generate_html()

# ── HTML Generation ──────────────────────────────────────────────────────────

def get_date_class(date_str: str) -> str:
    TODAY = datetime.now().strftime("%Y-%m-%d")
    WEEK_AGO = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    if not date_str:
        return "date-tag"
    if date_str == TODAY:
        return "date-tag date-today"
    if date_str >= WEEK_AGO:
        return "date-tag date-recent"
    return "date-tag"

def format_price(val) -> str:
    if val in (None, "", "N/A"):
        return "-"
    try:
        num = float(str(val).replace(",", "").replace("$", ""))
        if num < 0.01:
            return f"${num:.4f}"
        elif num < 1:
            return f"${num:.3f}"
        else:
            return f"${num:.2f}"
    except (ValueError, TypeError):
        return str(val)

def get_diff_class(diff_val) -> str:
    if diff_val in (None, "", "N/A"):
        return "price-na"
    try:
        num = float(str(diff_val).replace("%", ""))
        if num > 0:
            return "price-up"
        elif num < 0:
            return "price-down"
        return "price-flat"
    except (ValueError, TypeError):
        return "price-na"

def format_diff(diff_val) -> str:
    if diff_val in (None, "", "N/A"):
        return "N/A"
    try:
        num = float(str(diff_val).replace("%", ""))
        sign = "+" if num > 0 else ""
        return f"{sign}{num:.1f}%"
    except (ValueError, TypeError):
        return str(diff_val)

def build_row(placement: dict) -> str:
    code = html.escape(str(placement.get("ASX_Code", "")))
    company = html.escape(str(placement.get("Company", "")))
    headline = html.escape(str(placement.get("Headline", "")))
    date_str = str(placement.get("Date", ""))
    cr_price = placement.get("CR_Price", "")
    cur_price = placement.get("Current_Price", "")
    diff_pct = placement.get("Price_Diff_%", "")
    pdf_link = str(placement.get("PDF_Link", ""))

    date_cls = get_date_class(date_str)
    diff_cls = get_diff_class(diff_pct)

    row = '<tr>\n'
    row += f'  <td>\n    <div class="ticker">{code}</div>\n'
    if company:
        row += f'    <div class="company-name">{company}</div>\n'
    row += '  </td>\n'
    row += f'  <td>\n    <span class="{date_cls}">{html.escape(date_str)}</span>\n  </td>\n'
    row += f'  <td>\n    <span class="event-pill e-cr">{headline}</span>\n  </td>\n'

    price_display = format_price(cr_price)
    if price_display == "-":
        row += '  <td>\n    <span style="color:#ccc;font-size:10px;">-</span>\n  </td>\n'
    else:
        row += f'  <td>\n    <span class="cr-val price-flat">{price_display}</span>\n  </td>\n'

    cur_display = format_price(cur_price)
    if cur_display == "-":
        row += '  <td>\n    <span style="color:#ccc;font-size:10px;">-</span>\n  </td>\n'
    else:
        row += f'  <td>\n    <span style="font-size:11px; font-weight:500; color:#333;">{cur_display}</span>\n  </td>\n'

    diff_display = format_diff(diff_pct)
    if diff_display == "N/A":
        row += '  <td>\n    <span class="diff-val price-na">N/A</span>\n  </td>\n'
    else:
        row += f'  <td>\n    <span class="diff-val {diff_cls}">{diff_display}</span>\n  </td>\n'

    if pdf_link:
        row += f'  <td>\n    <a class="pdf-link" href="{html.escape(pdf_link)}" target="_blank">📄 PDF</a>\n  </td>\n'
    else:
        row += '  <td>\n    <span style="color:#ccc;font-size:10px;">-</span>\n  </td>\n'

    row += '</tr>\n'
    return row

def generate_html(save_file: bool = True) -> str:
    root = os.path.dirname(os.path.abspath(__file__))
    yaml_file = os.path.join(os.path.abspath(os.path.join(root, "..", "config")), "asx_placements.yaml")
    html_out = os.path.join(os.path.abspath(os.path.join(root, "..", "output")), "asx_placements.html")
    template_path = os.path.join(os.path.abspath(os.path.join(root, "..", "templates")), "asx_placements.html")

    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            placements = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: YAML config not found at {yaml_file}")
        return ""
    except Exception as e:
        print(f"Error loading YAML from {yaml_file}: {e}")
        return ""

    if not placements:
        print("No placements data found in YAML.")
        return ""

    placements.sort(key=lambda x: str(x.get("Date", "")), reverse=True)

    rows_html = ""
    for p in placements:
        rows_html += build_row(p)

    ranked = []
    for p in placements:
        diff = p.get("Price_Diff_%", "")
        if diff in (None, "", "N/A"):
            continue
        try:
            diff_num = float(str(diff).replace("%", ""))
            ranked.append((str(p.get("ASX_Code", "")), diff_num))
        except (ValueError, TypeError):
            continue

    ranked.sort(key=lambda x: x[1], reverse=True)
    top_10 = ranked[:10]

    bg_colors = [
        ("#E24B4A", "#4A0808"), ("#E24B4A", "#4A0808"), ("#E24B4A", "#4A0808"),
        ("#EF9F27", "#412402"), ("#EF9F27", "#412402"), ("#EF9F27", "#412402"),
        ("#1D9E75", "#04342C"), ("#1D9E75", "#04342C"), ("#1D9E75", "#04342C"), ("#1D9E75", "#04342C")
    ]

    ranking_html = ""
    for i, (code, diff) in enumerate(top_10):
        bg, col = bg_colors[i] if i < len(bg_colors) else ("#eee", "#333")
        sign = "+" if diff > 0 else ""
        ranking_html += (
            f'      <div style="display:flex; align-items:center; gap:8px; font-size:12px;">'
            f'<span style="background:{bg}; color:{col}; padding:2px 8px; border-radius:99px; '
            f'font-size:10px; font-weight:500;">{i+1}</span>'
            f'{code} — {sign}{diff:.1f}%</div>\n'
        )

    dates = [str(p.get("Date", "")) for p in placements if p.get("Date")]
    min_date = min(dates) if dates else "N/A"
    max_date = max(dates) if dates else "N/A"
    stats_text = f"共 {len(placements)} 条 · {min_date} — {max_date}"

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    final_html = (
        template
        .replace("{{ table_rows }}", rows_html)
        .replace("{{ ranking_html }}", ranking_html)
        .replace("{{ stats_text }}", stats_text)
    )

    if save_file:
        os.makedirs(os.path.dirname(html_out), exist_ok=True)
        with open(html_out, 'w', encoding='utf-8') as f:
            f.write(final_html)
        print(f"Generated {html_out} successfully with {len(placements)} placements.")
    
    return final_html


if __name__ == "__main__":
    main()
