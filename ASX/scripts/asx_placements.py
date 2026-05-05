"""
ASX Placement Scanner (Best Practice Refactor)

Detailed extraction of capital raising events.
Implements Global Price Refresh with optimized bulk updates.
"""

import argparse
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

import pdfplumber
import requests
import yaml

try:
    from pdf_cache import download_pdf, get_cache_dir
    from schemas import PlacementSchema
    from utils import (
        DEFAULT_MCAP_FILTER,
        DEFAULT_TIMEOUT,
        get_all_known_stocks,
        get_asx_pdf_url,
        get_http_session,
        get_pdf_filename,
        get_root_dir,
        get_sydney_time,
        load_config,
        load_yaml_data,
        logger,
        normalize_date,
        save_yaml_data,
        ticker_clean,
    )
except ImportError:
    from scripts.pdf_cache import download_pdf, get_cache_dir
    from scripts.schemas import PlacementSchema
    from scripts.utils import (
        DEFAULT_MCAP_FILTER,
        DEFAULT_TIMEOUT,
        get_all_known_stocks,
        get_asx_pdf_url,
        get_http_session,
        get_pdf_filename,
        get_root_dir,
        get_sydney_time,
        load_config,
        load_yaml_data,
        logger,
        normalize_date,
        save_yaml_data,
        ticker_clean,
    )

# --- Configuration ---
_CFG = load_config()
_API = _CFG.get("api", {})
API_BASE = _API.get("announcements_base", "https://asx.api.markitdigital.com/asx-research/1.0/markets/announcements")
PRICE_API = _API.get("company_header", "https://asx.api.markitdigital.com/asx-research/1.0/companies/{}/header")
ITEMS_PER_PAGE = _CFG.get("scanners", {}).get("items_per_page", 1000)

_WORKERS = int(_CFG.get("concurrency", {}).get("placements_workers", 20))
_PLACEMENTS_CFG = _CFG.get("placements", {})

PLACEMENT_KEYWORDS = tuple(
    _PLACEMENTS_CFG.get(
        "keywords",
        [
            "placement",
            "capital rais",
            "capital raise",
            "share purchase plan",
            "spp",
            "equity raising",
            "entitlement offer",
            "rights issue",
        ],
    )
)

PLACEMENT_REGEX_PATTERNS = tuple(
    _PLACEMENTS_CFG.get(
        "headline_patterns",
        [
            r"\braise(?:s|d)?\s+a\$\s*\d",
            r"\bto\s+fund\b",
            r"\bfirm\s+commitments\b",
            r"\bcommitments\s+received\b",
        ],
    )
)

_CACHE_DIR = get_cache_dir()


class PlacementScanner:
    """Encapsulates the capital raising extraction and sync logic."""

    def __init__(self, session: requests.Session):
        self.session = session
        self.overrides = self._load_overrides()

    def _download_pdf(self, url: str, filename: str) -> Path | None:
        return download_pdf(
            self.session,
            url,
            filename,
            cache_dir=_CACHE_DIR,
            timeout=DEFAULT_TIMEOUT,
            logger=logger,
        )

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

    def extract_cr_price(self, text: str, is_content: bool = False) -> float:
        """Heuristic to extract CR price from text (headline or content).
        Avoids picking up total amounts (e.g. $5m) as per-share price.
        """
        if not text:
            return 0.0
        txt = text.lower()

        # Currency prefix (e.g. $, A$, US$, AUD$)
        dsym = r"(?:[a-z]{1,3})?\$"

        # 1. Cents Pattern: 15c, 15 cents, 15.5c, 15.5cps
        cent_patterns = [
            r"\b(\d+\.?\d*)\s*(?:c|cents?|cps)\b(?!\s*(?:m|million|b|billion))",
            r"(?:at|@|of)\s*(\d+\.?\d*)\s*(?:c|cents?|cps)",
            r"(?:price|issue|offer|conversion)\s*[:]?\s*(?:of|at)?\s*[:]?\s*(\d+\.?\d*)\s*(?:c|cents?|cps)",
        ]
        for p in cent_patterns:
            match = re.search(p, txt)
            if match:
                try:
                    val = float(match.group(1))
                    if val > 1000:
                        continue
                    return round(val / 100.0, 4)
                except ValueError:
                    continue

        # 2. Dollar Patterns (issue price, at $0.15 etc)
        dollar_patterns = [
            rf"(?:at|@|priced)\s*(?:at)?\s*[:]?\s*{dsym}?\s*(\d+\.\d+)\s*(?:per\s*share|each|a\s+share|(?!\s*(?:m|mln|million|b|bln|billion))\b)",
            rf"(?:price|issue|offer|conversion)\s*[:]?\s*(?:of|at)?\s*[:]?\s*{dsym}?\s*(\d+\.?\d+)",
            rf"{dsym}(\d+\.\d+)\s*per\s*share",
            rf"at\s+a\s+price\s+of\s+{dsym}?(\d+\.\d+)",
        ]
        for p in dollar_patterns:
            match = re.search(p, txt)
            if match:
                try:
                    val = float(match.group(1))
                    if val > 500:
                        continue
                    return val
                except ValueError:
                    continue

        # 3. Fallback: Simple dollar match with broad negative lookahead
        # ONLY apply to headlines to avoid false positives in noisy PDF content
        if not is_content:
            fallback_patterns = [
                rf"{dsym}(\d+\.\d+)\b(?!\s*(?:m|mln|million|b|bln|billion))",
                r"(?:at|@)\s*[:]?\s*(\d+\.\d+)\b(?!\s*(?:c|cent|m|mln|million|b|bln|billion))",
            ]
            for p in fallback_patterns:
                match = re.search(p, txt)
                if match:
                    try:
                        val = float(match.group(1))
                        if 0.0001 < val < 500:
                            return val
                    except ValueError:
                        continue

        return 0.0

    def calculate_diff(self, cur: float, cr: float) -> float:
        """Calculate percentage difference between current price and CR price."""
        if not cur or not cr:
            return 0.0
        return round(((cur - cr) / cr) * 100, 2)

    def _load_overrides(self) -> dict:
        """Load manual overrides from config/placement_overrides.yaml."""
        path = get_root_dir() / "config" / "placement_overrides.yaml"
        if not path.exists():
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                overrides_list = data.get("overrides") or []
                return {ticker_clean(o["symbol"]): o for o in overrides_list}
        except Exception as e:
            logger.error(f"Failed to load overrides: {e}")
            return {}

    def fetch_market_info(self, symbol: str) -> tuple[float | None, int | None, str | None, str | None]:
        """Fetch current price, market cap, and display name from ASX Header API."""
        try:
            r = self.session.get(PRICE_API.format(symbol.upper()), timeout=DEFAULT_TIMEOUT)
            if r.status_code == 200:
                d = r.json().get("data", {})
                return d.get("priceLast"), d.get("marketCap"), d.get("displayName"), d.get("issueType")
        except:
            pass
        return None, None, None, None

    def process_raw(self, items: list[dict]) -> list[dict]:
        """Heuristic filter for placement announcements."""
        processed = []
        for item in items:
            hl = item.get("headline", "").lower()
            # Use \b at the start of the keyword to ensure we match "placement" but not "replacement"
            is_keyword_match = any(re.search(rf"\b{re.escape(kw)}", hl) for kw in PLACEMENT_KEYWORDS)
            is_pattern_match = any(re.search(pattern, hl) for pattern in PLACEMENT_REGEX_PATTERNS)
            if is_keyword_match or is_pattern_match:
                processed.append(
                    {
                        "symbol": ticker_clean(item.get("symbol", "")),
                        "date": normalize_date(item.get("date", "")),
                        "company": item.get("companyInfo")[0].get("displayName", "") if item.get("companyInfo") else "",
                        "headline": hl,
                        "pdf_link": get_asx_pdf_url(item.get("documentKey", ""), item.get("date", "")),
                        "documentKey": item.get("documentKey", ""),
                        "issueType": item.get("companyInfo")[0].get("issueType", "") if item.get("companyInfo") else "",
                    }
                )
        return processed

    def refresh_all_prices(self):
        """Global Update: Fetch current prices for ALL placements in YAML."""
        logger.info("Performing Global Price Refresh for all placements...")
        placements = load_yaml_data("asx_placements.yaml")
        if not placements:
            return

        symbols = list(set(p["ASX_Code"] for p in placements if "ASX_Code" in p))
        price_map = {}

        with ThreadPoolExecutor(max_workers=_WORKERS) as ex:
            results = ex.map(lambda s: (s, self.fetch_market_info(s)), symbols)
            for sym, (px, _mcap, name, _itype) in results:
                if px is not None:
                    price_map[sym] = {"price": px, "name": name}

        updated = 0
        for p in placements:
            sym = p.get("ASX_Code")
            meta = price_map.get(sym)
            if meta:
                p["Current_Price"] = meta["price"]
                if meta["name"] and (not p.get("Company") or p.get("Company") == ""):
                    p["Company"] = meta["name"]

                if p.get("CR_Price") and p["CR_Price"] > 0:
                    p["Price_Diff_%"] = round(((p["Current_Price"] - p["CR_Price"]) / p["CR_Price"]) * 100, 2)
                updated += 1

        save_yaml_data("asx_placements.yaml", placements)
        logger.info(f"Global Update: Refreshed {updated} records.")

    def sync_to_yaml(self, events: list[dict]):
        """Standard sync with overrides and validation."""
        added = 0
        updated = 0
        skipped_low_mcap = 0

        placements = load_yaml_data("asx_placements.yaml")
        existing_map = {p["ASX_Code"]: p for p in placements if "ASX_Code" in p}
        known_stocks = get_all_known_stocks()

        # --- Phase 1: Apply delete/exclude overrides ---
        eligible_events = []
        for ev in events:
            sym = ev["symbol"]
            ov = self.overrides.get(sym, {})
            if ov.get("delete") or ov.get("exclude"):
                if sym in existing_map:
                    del existing_map[sym]
                continue
            eligible_events.append(ev)

        # --- Phase 2: Batch-fetch market info for all symbols ---
        unique_symbols = list(set(ev["symbol"] for ev in eligible_events))
        market_cache = {}

        with ThreadPoolExecutor(max_workers=_WORKERS) as ex:
            results = ex.map(lambda s: (s, self.fetch_market_info(s)), unique_symbols)
            for sym, (px, mcap, name, itype) in results:
                market_cache[sym] = {"price": px, "mcap": mcap, "name": name, "issueType": itype}

        # --- Phase 3: Filter by market cap (liquidity gate) ---
        liquid_events = []
        for ev in eligible_events:
            sym = ev["symbol"]
            info = market_cache.get(sym, {})
            mcap = info.get("mcap")

            if mcap and mcap < DEFAULT_MCAP_FILTER:
                skipped_low_mcap += 1
                continue

            issue_type = info.get("issueType")
            if not issue_type:
                if sym not in known_stocks:
                    continue

            if issue_type and issue_type not in ["CS", "CD", "ET", "UI"]:
                continue

            if len(sym.replace(".AX", "")) > 4:
                continue

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

            existing = existing_map.get(sym)
            new_date = datetime.strptime(ev["date"], "%Y-%m-%d").date()

            cr_price = ov.get("cr_price")
            existing_event_date = (
                datetime.strptime(existing["Date"], "%Y-%m-%d").date()
                if existing and existing.get("Date")
                else datetime.min.date()
            )

            already_processed = (
                existing and existing.get("CR_Price") and existing["CR_Price"] > 0 and new_date >= existing_event_date
            )

            if not cr_price and not already_processed:
                cr_price = self.extract_cr_price(ev["headline"])
                if not cr_price or cr_price == 0.0:
                    fname = get_pdf_filename(ev)
                    local_pdf = self._download_pdf(ev["pdf_link"], fname)
                    if local_pdf:
                        content = self._extract_text_from_pdf(local_pdf)
                        if content:
                            cr_price = self.extract_cr_price(content, is_content=True)
                            if cr_price > 0:
                                logger.info(f"Extracted CR Price {cr_price} from content for {sym}")
            elif already_processed:
                cr_price = existing["CR_Price"]

            if existing:
                if ov.get("cr_price") is not None:
                    existing["CR_Price"] = ov["cr_price"]
                    existing["Current_Price"] = cur_px or existing.get("Current_Price", 0.0)
                    existing["Price_Diff_%"] = self.calculate_diff(existing["Current_Price"], existing["CR_Price"])
                    updated += 1
                else:
                    has_new_price = cr_price and cr_price > 0
                    has_old_price = existing.get("CR_Price") and existing["CR_Price"] > 0

                    should_replace = False
                    if has_new_price and not has_old_price:
                        should_replace = True
                    elif has_new_price == has_old_price:
                        if new_date < existing_event_date:
                            should_replace = True

                    if has_old_price and not has_new_price:
                        hl_low = existing.get("Headline", "").lower()
                        if any(x in hl_low for x in ["m", "million", "b", "billion"]):
                            pattern = rf"{re.escape(str(existing['CR_Price']))}\s*[mb]"
                            if re.search(pattern, hl_low):
                                existing["CR_Price"] = 0.0
                                should_replace = True

                    if should_replace:
                        existing["Date"] = ev["date"]
                        existing["Headline"] = ev["headline"]
                        existing["CR_Price"] = cr_price
                        existing["PDF_Link"] = ev["pdf_link"]
                        existing["Current_Price"] = cur_px or existing.get("Current_Price", 0.0)
                        existing["Price_Diff_%"] = self.calculate_diff(existing["Current_Price"], existing["CR_Price"])
                        updated += 1
                    else:
                        existing["Current_Price"] = cur_px or existing.get("Current_Price", 0.0)
                        if existing.get("CR_Price") and existing["CR_Price"] > 0:
                            existing["Price_Diff_%"] = self.calculate_diff(
                                existing["Current_Price"], existing["CR_Price"]
                            )
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
                        "PDF_Link": ev["pdf_link"],
                    }
                    v = PlacementSchema(**p_data)
                    existing_map[sym] = v.model_dump()
                    added += 1
                except Exception as e:
                    logger.error(f"Placement validation failed for {sym}: {e}")

        # Keep only the last 3000 placements
        placements_list = list(existing_map.values())
        placements_list.sort(key=lambda x: str(x.get("Date", "")), reverse=True)
        placements_list = placements_list[:3000]

        save_yaml_data("asx_placements.yaml", placements_list)
        logger.info(f"Sync Complete: Added {added}, Updated {updated}.")

    def apply_forced_overrides(self):
        """Handle manual overrides (price updates and deletions) globally for all matched symbols."""
        logger.info("Applying global forced overrides...")
        placements = load_yaml_data("asx_placements.yaml")
        existing_map = {p["ASX_Code"]: p for p in placements if "ASX_Code" in p}

        for sym, ov in self.overrides.items():
            if ov.get("delete") or ov.get("exclude"):
                if sym in existing_map:
                    del existing_map[sym]
                    logger.info(f"Globally excluded/deleted: {sym}")
                continue

            if ov.get("cr_price"):
                older = existing_map.get(sym)
                if older and older.get("CR_Price") != ov["cr_price"]:
                    older["CR_Price"] = ov["cr_price"]
                    if older.get("Current_Price") and older["CR_Price"] > 0:
                        older["Price_Diff_%"] = self.calculate_diff(older["Current_Price"], older["CR_Price"])
                    logger.info(f"Forced manual price override: {sym} -> {ov['cr_price']}")

        save_yaml_data("asx_placements.yaml", list(existing_map.values()))


def main():
    parser = argparse.ArgumentParser(description="ASX Placement Scanner")
    parser.add_argument("--months", type=int, default=0)
    parser.add_argument("--full-refresh", action="store_true")
    args = parser.parse_args()

    session = get_http_session()

    scanner = PlacementScanner(session)

    # 1. Scrape News
    start_date = get_sydney_time() - timedelta(days=args.months * 30)

    if not args.full_refresh:
        placements = load_yaml_data("asx_placements.yaml")
        if placements:
            max_dt_str = max([str(p.get("Date", "")) for p in placements])
            if max_dt_str:
                latest_date = datetime.strptime(max_dt_str, "%Y-%m-%d")
                recent_cutoff = get_sydney_time() - timedelta(days=2)
                start_date = max(latest_date, recent_cutoff.replace(tzinfo=None))
                logger.info(f"Resuming placements from {start_date:%Y-%m-%d}...")

    params = {
        "dateStart": start_date.strftime("%Y-%m-%d"),
        "dateEnd": (get_sydney_time() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "itemsPerPage": ITEMS_PER_PAGE,
        "page": 0,
    }

    raw_announcements = []
    while True:
        r = session.get(API_BASE, params=params, timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:
            break
        items = r.json().get("data", {}).get("items", [])
        if not items:
            break
        raw_announcements.extend(items)
        if len(raw_announcements) >= r.json().get("data", {}).get("count", 0):
            break
        params["page"] += 1
        time.sleep(0.3)

    # 2. Extract & Sync
    events = scanner.process_raw(raw_announcements)
    scanner.sync_to_yaml(events)

    # 3. Global Forced Overrides (Sync YAML state)

    # 4. Global Refresh (Fetch latest market prices)
    scanner.refresh_all_prices()


if __name__ == "__main__":
    main()
