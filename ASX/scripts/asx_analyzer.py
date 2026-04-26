"""
ASX Market Momentum Analyzer (Best Practice Refactor)

Calculates technical momentum metrics (RSI, EMA, Score) for all watched stocks.
Enriches data with fundamental descriptors from the ASX Header API.
"""

import argparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests
import yfinance as yf

try:
    from db_manager import db
    from db_models import MarketTrend, Stock
    from db_schemas import MarketTrendSchema
    from utils import (
        get_http_session,
        get_sydney_time,
        load_config,
        logger,
        print_progress,
    )
except ImportError:
    from scripts.db_manager import db
    from scripts.db_models import MarketTrend, Stock
    from scripts.db_schemas import MarketTrendSchema
    from scripts.utils import (
        get_http_session,
        get_sydney_time,
        load_config,
        logger,
        print_progress,
    )

# --- Configuration ---
_CFG = load_config()
_API = _CFG.get("api", {})
DESC_API = _API.get("company_header", "https://asx.api.markitdigital.com/asx-research/1.0/companies/{}/header")
STATS_API = "https://asx.api.markitdigital.com/asx-research/1.0/companies/{}/key-statistics"

_WORKERS = int(_CFG.get("concurrency", {}).get("analyzer_workers", 10))
_HTTP_CFG = _CFG.get("http", {})
_FUNDAMENTALS_CONNECT_TIMEOUT = float(_HTTP_CFG.get("analyzer_connect_timeout_seconds", 8))
_FUNDAMENTALS_READ_TIMEOUT = float(_HTTP_CFG.get("analyzer_read_timeout_seconds", 15))


class MomentumAnalyzer:
    """Analyzes technical and fundamental metrics for a list of tickers."""

    def __init__(self, session: requests.Session):
        self.session = session

    def standardize_text(self, text: str | None) -> str:
        """Standardize industry/name strings (Title Case, trim, remove clutter)."""
        if not text or text.lower() in ["none", "n/a", "-"]:
            return "Other"

        # Remove common clutter
        text = re.sub(r"\(REITs\)", "", text, flags=re.IGNORECASE)
        text = re.sub(r" Group$", "", text, flags=re.IGNORECASE)

        return text.strip().title()

    def fetch_fundamentals(self, symbol: str) -> dict[str, Any]:
        """Fetch fundamental descriptors and stats from ASX API."""
        out = {}
        try:
            # 1. Basic Header (Market Cap, Industry)
            r1 = self.session.get(
                f"{DESC_API.format(symbol.upper())}",
                timeout=(_FUNDAMENTALS_CONNECT_TIMEOUT, _FUNDAMENTALS_READ_TIMEOUT),
            )
            if r1.status_code == 200:
                out.update(r1.json().get("data", {}))

            # 2. Key Statistics (PE, Yield)
            r2 = self.session.get(
                f"{STATS_API.format(symbol.upper())}",
                timeout=(_FUNDAMENTALS_CONNECT_TIMEOUT, _FUNDAMENTALS_READ_TIMEOUT),
            )
            if r2.status_code == 200:
                stats = r2.json().get("data", {})
                # Normalize keys for easier mapping
                out["pe"] = stats.get("priceEarningsRatio")
                out["yield_val"] = stats.get("yieldAnnual")
        except Exception as e:
            logger.debug(f"Fundamental fetch failed for {symbol}: {e}")
        return out

    def calculate_rsi(self, series, period: int = 14) -> float:
        """Calculate Relative Strength Index using Wilder's Smoothing (Matching TradingView)."""
        if len(series) <= period:
            return 50.0

        delta = series.diff().dropna()
        ups = delta.clip(lower=0)
        downs = -1 * delta.clip(upper=0)

        # Initial SMA for the first period
        avg_gain = [ups[:period].mean()]
        avg_loss = [downs[:period].mean()]

        # Wilder's Smoothing: (Prev_Avg * 13 + Curr_Val) / 14
        alpha = 1 / period
        for i in range(period, len(ups)):
            avg_gain.append(avg_gain[-1] * (1 - alpha) + ups.iloc[i] * alpha)
            avg_loss.append(avg_loss[-1] * (1 - alpha) + downs.iloc[i] * alpha)

        last_gain = avg_gain[-1]
        last_loss = avg_loss[-1]

        if last_loss == 0:
            return 100.0 if last_gain > 0 else 50.0

        rs = last_gain / last_loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi)

    def analyze_ticker(
        self, symbol: str, stock_type: str
    ) -> tuple[MarketTrendSchema, tuple[str | None, str | None]] | None:
        """Process a single ticker for technical and fundamental data."""
        try:
            # 1. Fundamentals via ASX API (Primary for current price and metadata)
            funds = self.fetch_fundamentals(symbol)
            mcap = funds.get("marketCap")
            pe = funds.get("pe")
            yield_v = funds.get("yield_val")
            industry = self.standardize_text(funds.get("industryGroup"))
            comp_name = funds.get("displayName")
            live_px = funds.get("priceLast")
            live_chg_1d = funds.get("priceChange")
            live_diff_1d = funds.get("priceChangePercent")

            # 2. Technicals via yfinance (Fetch 6 months for indicator convergence)
            asx_sym = f"{symbol}.AX"
            ticker = yf.Ticker(asx_sym)
            hist = ticker.history(period="6mo")
            if hist.empty:
                return None

            close = hist["Close"]
            # Prioritize Live API price over yfinance
            curr_px = live_px if live_px is not None else close.iloc[-1]
            prev_px = close.iloc[-2] if len(close) > 1 else curr_px
            px_5d = close.iloc[-5] if len(close) > 5 else close.iloc[0]

            if live_chg_1d is not None and live_diff_1d is not None:
                price_change_1d = round(live_chg_1d, 4)
                price_diff_1d = round(live_diff_1d, 2)
            else:
                price_change_1d = round(curr_px - prev_px, 4)
                price_diff_1d = round((price_change_1d / prev_px) * 100, 2) if prev_px else 0
            price_change_5d = round(curr_px - px_5d, 4)
            price_diff_5d = round((price_change_5d / px_5d) * 100, 2) if px_5d else 0

            # Momentum proxies
            volatility = round(close.pct_change(fill_method=None).std() * 100, 2)
            momentum = round((curr_px - close.mean()) / close.std(), 2) if close.std() > 0 else 0
            rsi = round(self.calculate_rsi(close), 2)

            # Volume change
            vol_mean = hist["Volume"].mean()
            vol_last = hist["Volume"].iloc[-1]
            vol_change = round((vol_last - vol_mean) / vol_mean * 100, 2) if vol_mean > 0 else 0

            # 3. Scoring logic
            metrics = {
                "price_diff_1d": price_diff_1d,
                "price_diff_5d": price_diff_5d,
                "momentum": momentum,
                "vol_change": vol_change,
                "rsi": rsi,
            }
            score = self.calculate_score(metrics)

            return MarketTrendSchema(
                symbol=symbol,
                market_date=get_sydney_time().date(),
                current_price=curr_px,
                price_diff_1d=price_diff_1d,
                price_change_1d=price_change_1d,
                price_diff_5d=price_diff_5d,
                price_change_5d=price_change_5d,
                momentum=momentum,
                volatility=volatility,
                volume=int(hist["Volume"].iloc[-1]),
                volume_change=vol_change,
                rsi=rsi,
                score=round(score, 1),
                price_history=",".join([f"{p:.3f}" for p in close.tail(10).values]),
                market_cap=mcap,
                pe=pe,
                yield_val=yield_v,
            ), (industry, comp_name)
        except Exception as e:
            logger.error(f"Analysis failed for {symbol}: {e}")
            return None, (None, None)

    def calculate_score(self, m: dict[str, float]) -> float:
        """Proprietary scoring math based on various indicators."""
        score = 50.0  # Neural base

        # Trend indicators
        if m["rsi"] < 30:
            score += 10
        if m["rsi"] > 70:
            score -= 5

        # Momentum
        score += m["momentum"] * 5

        # Price Action
        score += m["price_diff_1d"] * 2
        score += m["price_diff_5d"] * 1.5

        # Volume
        if m["vol_change"] > 50:
            score += 5

        return min(max(round(score, 1), 0), 100)

    def main_sync(self, include_announcement: bool = False, extra_symbols: list = None):
        """Analyze watched stocks and sync snapshots to DB."""
        logger.info("Starting Market Momentum Analysis...")
        with db.session_scope() as sess:
            # Selective Query: Only core types by default
            target_types = ["growth", "foundation", "etf"]
            if include_announcement:
                target_types.append("announcement")

            stocks = sess.query(Stock).filter(Stock.stock_type.in_(target_types)).all()

            # Append extra symbols (e.g. today's announcement tickers) not already covered
            if extra_symbols:
                covered = {s.symbol for s in stocks}
                extra = [
                    s
                    for s in sess.query(Stock).filter(Stock.symbol.in_(extra_symbols)).all()
                    if s.symbol not in covered
                ]
                stocks.extend(extra)

            if not stocks:
                logger.warning("No target stocks found in DB. Check stock_types.")
                return

            extra_label = f" +{len(extra_symbols or [])} extra" if extra_symbols else ""
            logger.info(f"Processing {len(stocks)} symbols (Target Types: {target_types}{extra_label})...")
            results = []

            # Parallelize analysis
            with ThreadPoolExecutor(max_workers=_WORKERS) as ex:
                futures = {ex.submit(self.analyze_ticker, s.symbol, s.stock_type): s for s in stocks}
                completed = 0
                succeeded = 0
                for future in as_completed(futures):
                    stock_obj = futures[future]
                    result = future.result()
                    completed += 1
                    if result:
                        res, meta = result
                        if res:
                            # UNIFIED RE-CRAWL: Always overwrite name/industry
                            if meta[0]:
                                stock_obj.industry = meta[0]
                            if meta[1]:
                                stock_obj.name = meta[1]
                            results.append(res)
                            succeeded += 1
                    if completed == len(stocks) or completed % max(1, min(10, _WORKERS)) == 0:
                        print_progress(
                            "Market analysis progress: "
                            f"{completed}/{len(stocks)} completed "
                            f"({succeeded} succeeded, {completed - succeeded} failed)"
                        )
                print()  # Newline after progress complete

            now = get_sydney_time()
            sync_count = 0

            for r in results:
                # Standard SCD Type 2 logic for snapshots
                # Check if a snapshot for THIS market_date already exists
                existing = sess.query(MarketTrend).filter_by(symbol=r.symbol, market_date=r.market_date).first()

                params = r.model_dump(exclude={"symbol"})

                if existing:
                    # Update existing snapshot for the day
                    for k, v in params.items():
                        setattr(existing, k, v)
                    existing.valid_from = now
                else:
                    # Retire old active record
                    sess.query(MarketTrend).filter_by(symbol=r.symbol, is_active=True).update(
                        {"is_active": False, "valid_to": now}
                    )
                    # Add new active record
                    new_trend = MarketTrend(symbol=r.symbol, is_active=True, valid_from=now, **params)
                    sess.add(new_trend)

                sync_count += 1

            logger.info(f"Market Analysis Complete: Synced {sync_count} snapshots.")


def main():
    parser = argparse.ArgumentParser(description="ASX Market Momentum Analyzer")
    parser.add_argument("--announcement", action="store_true", help="Include 'announcement' stocks in analysis")
    parser.add_argument("--extra-symbols", type=str, default="", help="Comma-separated extra symbols to include")
    args = parser.parse_args()

    extra = [s.strip() for s in args.extra_symbols.split(",") if s.strip()] if args.extra_symbols else None

    session = get_http_session()

    analyzer = MomentumAnalyzer(session)
    analyzer.main_sync(include_announcement=args.announcement, extra_symbols=extra)


if __name__ == "__main__":
    main()
