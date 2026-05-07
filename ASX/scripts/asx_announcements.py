"""
ASX Announcements Scraper (Best Practice Refactor)

Fetches general corporate announcements from the ASX/Markit API,
performs heuristic rating/summarization, and saves to YAML.
"""

import argparse
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

try:
    from pdf_cache import download_pdf, get_cache_dir
    from schemas import AnnouncementSchema
    from utils import (
        get_asx_pdf_url,
        get_http_session,
        get_pdf_filename,
        get_sydney_time,
        load_config,
        load_yaml_data,
        logger,
        normalize_date,
        print_progress,
        save_yaml_data,
        ticker_clean,
    )
except ImportError:
    from scripts.pdf_cache import download_pdf, get_cache_dir
    from scripts.schemas import AnnouncementSchema
    from scripts.utils import (
        get_asx_pdf_url,
        get_http_session,
        get_pdf_filename,
        get_sydney_time,
        load_config,
        load_yaml_data,
        logger,
        normalize_date,
        print_progress,
        save_yaml_data,
        ticker_clean,
    )

# --- Configuration ---
_CFG = load_config()
_API = _CFG.get("api", {})
API_BASE = _API.get("announcements_base", "https://asx.api.markitdigital.com/asx-research/1.0/markets/announcements")
ITEMS_PER_PAGE = _CFG.get("scanners", {}).get("items_per_page", 1000)
_PDF_WORKERS = int(_CFG.get("concurrency", {}).get("announcement_pdf_workers", 8))
_HTTP_CFG = _CFG.get("http", {})
_PDF_CONNECT_TIMEOUT = float(_HTTP_CFG.get("pdf_connect_timeout_seconds", 10))
_PDF_READ_TIMEOUT = float(_HTTP_CFG.get("pdf_read_timeout_seconds", 20))
_PDF_CHUNK_SIZE = int(_HTTP_CFG.get("pdf_chunk_size_bytes", 65536))
_PDF_MAX_ELAPSED_SECONDS = float(_HTTP_CFG.get("pdf_max_elapsed_seconds", 25))
_PDF_DISABLE_RETRIES = bool(_HTTP_CFG.get("pdf_disable_retries", True))

_CACHE_DIR = get_cache_dir()
_ANNOUNCEMENT_RATING_CFG = _CFG.get("announcement_rating", {})
COMPANY_HEADER_API = _API.get("company_header", "https://asx.api.markitdigital.com/asx-research/1.0/companies/{}/header")


NOISE_KEYWORDS = _ANNOUNCEMENT_RATING_CFG.get(
    "noise_keywords",
    [
        "appendix 4g",
        "appendix 3y",
        "change of director",
        "becoming a substantial holder",
        "ceasing to be",
        "notice of meeting",
        "proxy form",
        "disclosure notice",
        "shareholder letter",
        "investor presentation",
    ],
)

HIGH_VALUE_KEYWORDS = _ANNOUNCEMENT_RATING_CFG.get(
    "high_value_keywords",
    [
        "assay",
        "drilling",
        "high-grade",
        "discovery",
        "maiden",
        "resource",
        "phase 3",
        "fda",
        "approval",
        "exceptional",
        "breakthrough",
        "acquisition",
        "merger",
        "takeover",
        "binding",
        "offtake",
        "definitive",
        "feasibility study",
        "term sheet",
        "sale and purchase",
        "monetis",
        "partnership",
        "commerciali",
        "fast-track",
        "fast track",
        "commissioning",
        "first production",
    ],
)

STRONG_CATALYST_PHRASES = _ANNOUNCEMENT_RATING_CFG.get(
    "strong_catalyst_phrases",
    [
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
        "conditional spa",
    ],
)

MID_VALUE_KEYWORDS = _ANNOUNCEMENT_RATING_CFG.get(
    "mid_value_keywords",
    [
        "trading halt",
        "placement",
        "capital rais",
        "share purchase plan",
        "quarterly",
        "half year",
        "annual report",
        "guidance",
        "production",
        "revenue",
        "contract",
        "agreement",
        "joint venture",
        "feasibility",
        "scoping",
        "update",
        "progress",
        "operational",
        "upgrade",
        "milestone",
        "collaboration",
        "divest",
        "invest",
        "strategic",
        "joint venture",
        "restructur",
    ],
)


class AnnouncementScanner:
    """Encapsulates the announcement scraping and processing logic."""

    def __init__(self, session):
        self.session = session

    def _download_pdf(self, url: str, filename: str) -> Path | None:
        return download_pdf(
            self.session,
            url,
            filename,
            cache_dir=_CACHE_DIR,
            timeout=(_PDF_CONNECT_TIMEOUT, _PDF_READ_TIMEOUT),
            chunk_size=_PDF_CHUNK_SIZE,
            logger=logger,
            max_elapsed_seconds=_PDF_MAX_ELAPSED_SECONDS,
            disable_retries=_PDF_DISABLE_RETRIES,
        )

    def _download_pdfs_batch(self, downloads: list[tuple[str, str]]) -> None:
        """Download PDFs concurrently with de-duplication."""
        unique_downloads: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()
        skipped_cached = 0

        for url, filename in downloads:
            if not url or not filename:
                continue
            key = (url, filename)
            if key in seen:
                continue
            seen.add(key)
            if (_CACHE_DIR / filename).exists():
                skipped_cached += 1
                continue
            unique_downloads.append(key)

        if not unique_downloads:
            if skipped_cached:
                logger.info(f"All pending PDFs already cached ({skipped_cached} skipped).")
            return

        workers = max(1, min(_PDF_WORKERS, len(unique_downloads)))
        if workers == 1:
            for url, filename in unique_downloads:
                self._download_pdf(url, filename)
            return

        if skipped_cached:
            logger.info(
                f"Skipping {skipped_cached} cached PDFs. "
                f"Downloading {len(unique_downloads)} PDFs with {workers} workers..."
            )
        else:
            logger.info(f"Downloading {len(unique_downloads)} PDFs with {workers} workers...")
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(self._download_pdf, url, filename) for url, filename in unique_downloads]
            completed = 0
            succeeded = 0
            for future in as_completed(futures):
                result = future.result()
                completed += 1
                if result:
                    succeeded += 1
                if completed == len(unique_downloads) or completed % max(1, min(10, workers)) == 0:
                    print_progress(
                        "PDF download progress: "
                        f"{completed}/{len(unique_downloads)} completed "
                        f"({succeeded} succeeded, {completed - succeeded} failed)"
                    )
            print()  # Newline after progress complete

    def fetch_raw(self, start_date: datetime, *, price_sensitive_only: bool = True) -> list[dict]:
        """Fetch raw announcement JSON from ASX API."""
        end_date = get_sydney_time() + timedelta(days=1)

        params = {
            "dateStart": start_date.strftime("%Y-%m-%d"),
            "dateEnd": end_date.strftime("%Y-%m-%d"),
            "itemsPerPage": ITEMS_PER_PAGE,
            "page": 0,
        }

        all_items = []
        logger.info(f"Fetching announcements (from {start_date.strftime('%Y-%m-%d')})...")

        while True:
            try:
                r = self.session.get(API_BASE, params=params, timeout=30)
                r.raise_for_status()
                data = r.json()
                items = data.get("data", {}).get("items", [])
                if not items:
                    break

                if price_sensitive_only:
                    items = [
                        it for it in items if bool(it.get("isPriceSensitive") or it.get("priceSensitive") or False)
                    ]

                all_items.extend(items)
                count = data.get("data", {}).get("count", 0)
                if len(all_items) >= count:
                    break

                params["page"] += 1
                time.sleep(0.3)  # Rate limit respect
            except Exception as e:
                logger.error(f"API fetch failed on page {params['page']}: {e}")
                break

        return all_items

    @staticmethod
    def _load_rating_cfg() -> dict:
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

        text = (headline + " " + summary).lower()
        rating = 1
        reasons: list[str] = []

        # 1. Price Sensitive Bonus
        if is_price_sensitive:
            rating += cfg["price_sensitive_bonus"]
            reasons.append("price_sensitive")

        # 2. Data Impact Bonus (Regex for grades like 150g/t or 2.5%)
        if re.search(r"\d+(\.\d+)?\s*(g/t|%)", text):
            rating += 1
            reasons.append("impact_data")

        # 2b. Dollar Amount Bonus (e.g. "$15m", "$100 million", "A$50m")
        if re.search(r"\$\d+(\.\d+)?\s*(m|million|b|billion)", text):
            rating += 1
            reasons.append("dollar_amount")

        # 3. Phrase/Keyword Scoring
        strong_phrases = cfg["strong_catalyst_phrases"] or []
        high_keywords = cfg["high_value_keywords"] or []
        mid_keywords = cfg["mid_value_keywords"] or []

        # Check for literal strong phrases
        strong_hit = any(ph in text for ph in strong_phrases)

        # Check for major deal patterns (e.g., "Global MotoGP Deal", "Major Supply Contract")
        if not strong_hit:
            deal_pattern = (
                r"\b(global|major|transformational|exclusive|landmark)\b.*?\b"
                r"(deal|contract|agreement|partnership|alliance)\b"
            )
            if re.search(deal_pattern, text):
                strong_hit = True

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

    def fetch_market_data(self, tickers: set[str]) -> dict[str, dict[str, Any]]:
        """Fetch current prices and company names for a set of tickers in parallel."""
        data_map = {}
        if not tickers:
            return data_map

        def fetch_one(ticker):
            try:
                url = COMPANY_HEADER_API.format(ticker.upper())
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 200:
                    d = resp.json().get("data", {})
                    return ticker, d.get("priceLast"), d.get("displayName")
            except Exception:
                pass
            return ticker, None, None

        with ThreadPoolExecutor(max_workers=min(len(tickers), 20)) as executor:
            future_to_ticker = {executor.submit(fetch_one, t): t for t in tickers}
            for future in as_completed(future_to_ticker):
                ticker, price, name = future.result()
                data_map[ticker] = {"price": price, "name": name}
        return data_map

    def process_and_sync(self, raw_items: list[dict]):
        """Filter, validate, and save announcements to YAML (Latest Day Only)."""
        if not raw_items:
            logger.info("No raw items to process.")
            return

        # 1. Identify the latest date in the batch
        dates = [normalize_date(item.get("date", "")) for item in raw_items]
        max_date = max(dates) if dates else normalize_date(None)
        logger.info(f"Syncing announcements for the latest date: {max_date}")

        # 2. Filter raw items for the latest date only
        latest_raw = [item for item in raw_items if normalize_date(item.get("date", "")) == max_date]

        # 3. Gather tickers to fetch market data (prices & names)
        tickers_to_fetch = {ticker_clean(item.get("symbol", "")) for item in latest_raw if item.get("symbol")}
        market_map = self.fetch_market_data(tickers_to_fetch)

        # 4. Load existing for today (to avoid duplicates if run multiple times today)
        existing_ann = load_yaml_data("asx_announcements.yaml")
        # Keep items from other days if we want? No, user said "只保留最新一天"
        # So we only keep existing items if they are from max_date
        today_ann = [a for a in existing_ann if str(a.get("Date")) == max_date]
        existing_keys = {f"{a['ASX_Code']}_{a['Date']}_{a['Headline'][:100]}" for a in today_ann if "ASX_Code" in a}

        added = 0
        skipped = 0
        pending_downloads: list[tuple[str, str]] = []
        new_items = []

        for item in latest_raw:
            sym = ticker_clean(item.get("symbol", ""))
            hl = item.get("headline", "").strip()

            if not sym:
                continue

            ci = item.get("companyInfo")
            if ci and len(ci) > 0:
                issue_type = ci[0].get("issueType", "")
                if issue_type and issue_type not in ["CS", "CD", "ET", "UI"]:
                    skipped += 1
                    continue
                real_sym = ci[0].get("symbol", "")
                if real_sym and len(real_sym.replace(".AX", "")) > 4:
                    skipped += 1
                    continue

            if any(nk in hl.lower() for nk in NOISE_KEYWORDS):
                skipped += 1
                continue

            dt = max_date
            unique_key = f"{sym}_{dt}_{hl[:100]}"

            if unique_key in existing_keys:
                continue

            try:
                ann_types = item.get("announcementTypes", [])
                summary_text = ", ".join(ann_types) if ann_types else hl
                is_ps = bool(item.get("isPriceSensitive") or item.get("priceSensitive") or False)
                rating, rating_reason = self.calculate_rating_with_reason(hl, summary_text, is_ps)

                # 3-Tier Fallback Name Resolution:
                # 1. API announcement info (most specific)
                # 2. API header info (most reliable)
                # 3. Symbol (last resort)
                if ci and len(ci) > 0 and ci[0].get("displayName"):
                    company_name = ci[0]["displayName"]
                elif market_map.get(sym, {}).get("name"):
                    company_name = market_map[sym]["name"]
                else:
                    company_name = sym

                v = AnnouncementSchema(
                    ASX_Code=sym,
                    Company=company_name,
                    Headline=hl,
                    Summary=summary_text,
                    Date=dt,
                    PDF_Link=get_asx_pdf_url(item.get("documentKey", ""), dt),
                    Rating=rating,
                    Current_Price=round(market_map.get(sym, {}).get("price"), 4) if market_map.get(sym, {}).get("price") is not None else None,
                )

                new_items.append(v.model_dump())
                added += 1
                existing_keys.add(unique_key)

                if is_ps and v.PDF_Link:
                    pdf_ev = {"date": dt, "symbol": sym, "headline": hl}
                    pending_downloads.append((v.PDF_Link, get_pdf_filename(pdf_ev)))
            except Exception as e:
                logger.debug(f"Validation failed for announcement {unique_key}: {e}")

        # Final list = Existing today + New today
        final_list = today_ann + new_items
        # Sort by Rating desc, then Date desc (though all are same date here)
        final_list.sort(key=lambda x: (x.get("Rating", 0), str(x.get("Date", ""))), reverse=True)

        save_yaml_data("asx_announcements.yaml", final_list)

        logger.info(f"Sync Complete: Saved {len(final_list)} announcements for {max_date} (Added {added} new).")
        self._download_pdfs_batch(pending_downloads)

    def recalc_and_update(self, raw_items: list[dict]) -> None:
        """Recompute rating/rating_reason for announcements and update YAML rows if they exist."""
        updated = 0
        skipped = 0
        pending_downloads: list[tuple[str, str]] = []

        announcements = load_yaml_data("asx_announcements.yaml")
        ann_map = {f"{a['ASX_Code']}_{a['Date']}_{a['Headline'][:100]}": a for a in announcements if "ASX_Code" in a}

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

            ann = ann_map.get(unique_key)
            if not ann:
                continue

            ann_types = item.get("announcementTypes", [])
            summary_text = ", ".join(ann_types) if ann_types else (ann.get("Summary") or hl)
            is_ps = bool(item.get("isPriceSensitive") or item.get("priceSensitive") or False)

            rating, _ = self.calculate_rating_with_reason(hl, summary_text, is_ps)

            ann["Rating"] = rating
            if not ann.get("PDF_Link") or "asxpdf" in (ann.get("PDF_Link") or ""):
                ann["PDF_Link"] = get_asx_pdf_url(item.get("documentKey", ""), dt)
            updated += 1

            if is_ps and ann.get("PDF_Link"):
                pdf_ev = {"date": dt, "symbol": sym, "headline": hl}
                pending_downloads.append((ann["PDF_Link"], get_pdf_filename(pdf_ev)))

        if updated > 0:
            save_yaml_data("asx_announcements.yaml", announcements)

        logger.info(f"Recalc Complete: Updated {updated} announcements (Filtered {skipped} noise items).")
        self._download_pdfs_batch(pending_downloads)


def main():
    parser = argparse.ArgumentParser(description="ASX Announcement Scanner")
    parser.add_argument("--months", type=int, default=0)
    parser.add_argument("--full-refresh", action="store_true")
    parser.add_argument(
        "--recalc-days",
        type=int,
        default=0,
        help="Recalculate rating/rating_reason for the last N days of announcements fetched",
    )
    parser.add_argument(
        "--all-announcements", action="store_true", help="Fetch all announcements (otherwise only price-sensitive)"
    )
    args = parser.parse_args()

    session = get_http_session()

    scanner = AnnouncementScanner(session)

    # Calculate start_date (Priority: YAML Resumption > months argument)
    start_date = get_sydney_time() - timedelta(days=args.months * 30)
    if args.recalc_days and args.recalc_days > 0:
        start_date = get_sydney_time() - timedelta(days=args.recalc_days)

    if not args.full_refresh and not (args.recalc_days and args.recalc_days > 0):
        ann = load_yaml_data("asx_announcements.yaml")
        if ann:
            max_dt_str = max([str(a.get("Date", "")) for a in ann])
            if max_dt_str:
                start_date = datetime.strptime(max_dt_str, "%Y-%m-%d")
                logger.info(f"YAML check: Resuming from latest date {start_date.strftime('%Y-%m-%d')}")

    raw = scanner.fetch_raw(start_date, price_sensitive_only=not args.all_announcements)
    if args.recalc_days and args.recalc_days > 0:
        scanner.recalc_and_update(raw)
    scanner.process_and_sync(raw)


if __name__ == "__main__":
    main()
