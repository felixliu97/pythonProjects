"""
ASX Placement / Capital Raising Scanner

Scans ASX announcements for capital raising events, deduplicates by symbol
and date, extracts financial details from PDFs (multi-threaded), fetches
real-time prices, and outputs sortable numeric columns.

Supports incremental mode: reads existing CSV to resume from max_date + 1.
"""

import argparse
import csv
import io
import os
import re
import string
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

import requests

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

OUTPUT_FIELDS = [
    "ASX_Code",
    "Company",
    "Headline",
    "Date",
    "CR_Price",
    "Current_Price",
    "Price_Diff_%",
    "PDF_Link",
]


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
            if num is not None and 0.001 <= num <= 500.0:
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
                if 0.0001 <= final_val <= 1000.0:
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
            if 0.001 <= num <= 500.0:
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


def read_existing_csv(
    csv_path: str,
) -> Tuple[Optional[str], Set[str], List[Dict]]:
    """Read existing CSV and return (max_date, set of 'SYMBOL' keys, existing_rows)."""
    existing_symbols: Set[str] = set()
    max_date: Optional[str] = None
    existing_rows: List[Dict] = []

    if not os.path.exists(csv_path):
        return None, existing_keys, existing_rows

    try:
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sym = row.get("ASX_Code", "").strip()
                raw_date = row.get("Date", "").strip()
                date = normalize_date(raw_date)
                if sym and date:
                    existing_symbols.add(sym)
                    if max_date is None or date > max_date:
                        max_date = date
                    
                    norm_row = {
                        "symbol": sym,
                        "company": row.get("Company", ""),
                        "headline": row.get("Headline", ""),
                        "date": date,
                        "CR_Price": row.get("CR_Price", row.get("Price", "")),
                        "PDF_Link": row.get("PDF_Link", ""),
                    }
                    existing_rows.append(norm_row)
    except Exception as e:
        print(f"Warning: Could not read existing CSV: {e}")
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
        help="Ignore existing CSV; full re-scan and overwrite",
    )
    args = parser.parse_args()

    root = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.abspath(os.path.join(root, "..", ".pdf_cache"))
    os.makedirs(cache_dir, exist_ok=True)
    out_csv = os.path.join(root, "asx_placements.csv")

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36"
            ),
        }
    )

    # ── 0. Determine scan range from existing CSV ────────────────────────
    existing_symbols: Set[str] = set()
    start_override: Optional[str] = None
    existing_rows: List[Dict] = []
    fetch_new = True

    if not args.full_refresh:
        max_date, existing_symbols, existing_rows = read_existing_csv(out_csv)
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
                    f"(existing CSV max date: {max_date})"
                )
            else:
                print(
                    f"CSV is already up to date "
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

        # Skip if the symbol already exists in our master CSV
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
        
    all_events = processed_events + existing_rows

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

    # Sort descending by date
    rows.sort(key=lambda x: x["Date"], reverse=True)

    # ── 6. Write CSV — overwrite ─────────────────────────────────────────
    try:
        with open(
            out_csv, "w", newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(
                f, fieldnames=OUTPUT_FIELDS
            )
            writer.writeheader()
            writer.writerows(rows)
        print(
            f"\nExported {len(rows)} rows to: {out_csv}"
        )
    except PermissionError:
        alt_csv = out_csv.replace(".csv", "_new.csv")
        print(
            f"\nWarning: {out_csv} is locked. "
            f"Writing to {alt_csv} instead."
        )
        with open(
            alt_csv, "w", newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(
                f, fieldnames=OUTPUT_FIELDS
            )
            writer.writeheader()
            writer.writerows(rows)
        print(f"Exported to: {alt_csv}")


if __name__ == "__main__":
    main()
