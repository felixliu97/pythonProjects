"""
ASX Market Momentum & Trend Analyzer (Refactored)

Analyzes stock technicals (RSI, Momentum, Volatility) using yfinance data,
calculates custom scores, and syncs snapshots to PostgreSQL.
"""

import argparse
import json
import os
import sys
import time
import warnings
import concurrent.futures
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
import yfinance as yf
import yaml

# Local Imports
try:
    from db_manager import db
    from db_models import Stock, MarketTrend
    from db_schemas import MarketTrendSchema
    from utils import logger, get_root_dir, ticker_to_ax
except ImportError:
    from scripts.db_manager import db
    from scripts.db_models import Stock, MarketTrend
    from scripts.db_schemas import MarketTrendSchema
    from scripts.utils import logger, get_root_dir, ticker_to_ax

warnings.filterwarnings('ignore')

class ASXTrendingStocks:
    """Core analysis engine for ASX momentum and technical trends."""
    
    def __init__(self):
        self.root_dir = get_root_dir()
        self.config_file = self.root_dir / 'config' / 'asx_analyzer.yaml'
        self.output_dir = self.root_dir / 'output'
        self.cache_file = self.output_dir / 'asx_analyzer.json'
        self.output_dir.mkdir(exist_ok=True)
        
        self.settings = {"period": "1mo", "min_data_points": 10, "display_limit": 50}
        self._load_settings()

    def _load_settings(self):
        """Load settings from config/settings.yaml if available."""
        settings_path = self.root_dir / "config" / "settings.yaml"
        if settings_path.exists():
            with open(settings_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                self.settings.update(cfg.get("analyzer", {}))

    def fetch_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """Fetch historical price data in bulk with robust ticker mapping."""
        logger.info(f"Downloading data for {len(symbols)} symbols...")
        data_map = {}
        
        # Ensure all tickers have .AX suffix for download
        ax_tickers = list(set([ticker_to_ax(s) for s in symbols]))
        
        try:
            # Bulk download is much more efficient and stable than threading single calls
            df_all = yf.download(ax_tickers, period=self.settings["period"], interval="1d", progress=False, group_by='ticker')
            
            # Check if df_all is MultiIndex (multiple tickers) or standard (single ticker)
            is_multi = isinstance(df_all.columns, pd.MultiIndex)
            
            for s in symbols:
                ax_s = ticker_to_ax(s)
                try:
                    if is_multi:
                        if ax_s in df_all.columns.get_level_values(0):
                            # Use xs to robustly extract the sub-dataframe for the ticker
                            df_s = df_all.xs(ax_s, level=0, axis=1).dropna(subset=['Close'])
                            if not df_s.empty:
                                data_map[s] = df_s.copy()
                    else:
                        # Single successfully downloaded ticker might return standard DataFrame
                        if not df_all.empty:
                            data_map[s] = df_all.copy()
                except KeyError:
                    continue
        except Exception as e:
            logger.error(f"Bulk download failed: {e}")
            
        return data_map

    def calculate_rsi(self, series: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index."""
        if len(series) < period: return 50.0
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])

    def fetch_fundamentals(self, symbols: List[str]) -> Dict[str, Any]:
        """Fetch fundamental data (Info) for symbols using parallel execution."""
        logger.info(f"Fetching fundamental descriptors for {len(symbols)} tickers...")
        results = {}
        
        def get_info(s):
            try:
                ticker = yf.Ticker(ticker_to_ax(s))
                info = ticker.info
                # yfinance reports dividendYield as a fraction (0.04) or whole (4.0). 
                # Standards suggest fraction, but we verify to avoid 1000%+ bugs.
                raw_yield = info.get("dividendYield")
                cleaned_yield = 0.0
                if raw_yield:
                    if raw_yield > 1.0: # Likely already scaled (e.g., 4.5% as 4.5)
                        cleaned_yield = raw_yield
                    else: # Likely fraction (e.g., 0.045)
                        cleaned_yield = raw_yield * 100
                
                return s, {
                    "marketCap": info.get("marketCap"),
                    "pe": info.get("trailingPE") or info.get("forwardPE"),
                    "ps": info.get("priceToSalesTrailing12Months"),
                    "industry": info.get("industry") or info.get("sector"),
                    "yield": cleaned_yield
                }
            except Exception:
                return s, {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_info, s) for s in symbols]
            for future in concurrent.futures.as_completed(futures):
                s, info = future.result()
                if info: results[s] = info
        return results

    def analyze_stock(self, symbol: str, df: pd.DataFrame, stock_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Compute momentum, volatility, RSI and custom scores."""
        if len(df) < self.settings["min_data_points"]: return None
        
        close = df['Close'].values.flatten()
        vol = df['Volume'].values.flatten()
        
        cur_px = float(close[-1])
        px_5d = float(close[-5]) if len(close) >= 5 else float(close[0])
        px_1d = float(close[-2]) if len(close) >= 2 else float(close[0])
        
        # Historical price history for sparklines (comma separated)
        hist_prices = ",".join([str(round(float(p), 4)) for p in close[-30:]]) if len(close) >= 2 else str(cur_px)
        
        # Extract the date of the last bar for deduplication
        m_date = df.index[-1].date()
        
        # Metrics
        mom = ((cur_px - px_5d) / px_5d) * 100
        volat = (np.std(np.diff(close) / close[:-1])) * 100
        change_1d = ((cur_px - px_1d) / px_1d) * 100
        
        avg_vol = np.mean(vol[-10:]) if len(vol) >= 10 else np.mean(vol)
        vol_change = ((vol[-1] - avg_vol) / avg_vol) * 100 if avg_vol > 0 else 0
        
        rsi = float(self.calculate_rsi(df['Close']))
        
        # Basic Scoring logic (Momentum weighted)
        score = (mom * 0.4) + (vol_change * 0.1) - (volat * 0.1)
        if rsi > 70: score -= (rsi - 70) * 0.2 # Penalty for overbought
        if rsi < 30: score += (30 - rsi) * 0.3 # Bonus for oversold recovery

        return {
            "symbol": symbol,
            "name": stock_info.get("name", ""),
            "industry": stock_info.get("industry") or stock_info.get("sector", ""),
            "current_price": round(cur_px, 3),
            "score": round(score, 2),
            "price_change_1d": round(change_1d, 2),
            "price_diff_1d": round(cur_px - px_1d, 3),
            "price_change_5d": round(mom, 2),
            "price_diff_5d": round(cur_px - px_5d, 3),
            "momentum": round(mom, 2),
            "volatility": round(volat, 2),
            "volume_change": round(vol_change, 2),
            "rsi": round(rsi, 2),
            "marketCap": stock_info.get("marketCap"),
            "pe": stock_info.get("pe"),
            "ps": stock_info.get("ps"),
            "yield": stock_info.get("yield"),
            "price_history": hist_prices,
            "market_date": m_date.isoformat()
        }

    def save_to_db(self, data: List[Dict[str, Any]]):
        """Sync technical snapshots to DB using Pydantic validation."""
        session = db.get_session()
        count = 0
        now = datetime.now()
        
        for s in data:
            try:
                # 0. Sync Industry to Stock master table if missing
                if s.get('industry'):
                    stock = session.query(Stock).filter_by(symbol=s['symbol']).first()
                    if stock and not stock.industry:
                        stock.industry = s['industry']
                        session.flush()

                schema_input = {
                    "symbol": s.get('symbol'),
                    "current_price": s.get('current_price'),
                    "market_cap": s.get('marketCap'),
                    "pe": s.get('pe'),
                    "ps": s.get('ps'),
                    "yield_val": s.get('yield'),
                    "score": s.get('score'),
                    "price_change_1d": s.get('price_change_1d'),
                    "price_diff_1d": s.get('price_diff_1d'),
                    "price_change_5d": s.get('price_change_5d'),
                    "price_diff_5d": s.get('price_diff_5d'),
                    "momentum": s.get('momentum'),
                    "volatility": s.get('volatility'),
                    "volume_change": s.get('volume_change'),
                    "rsi": s.get('rsi'),
                    "price_history": s.get('price_history'),
                    "market_date": s.get('market_date')
                }
                v_trend = MarketTrendSchema(**schema_input)
                
                active_trend = session.query(MarketTrend).filter_by(symbol=v_trend.symbol, is_active=True).first()
                
                if active_trend:
                    # If it's the same market date, update the existing record with possibly new fundamental/history data
                    if active_trend.market_date == v_trend.market_date:
                        active_trend.current_price = v_trend.current_price
                        active_trend.market_cap = v_trend.market_cap
                        active_trend.pe = v_trend.pe
                        active_trend.ps = v_trend.ps
                        active_trend.yield_val = v_trend.yield_val
                        active_trend.score = v_trend.score
                        active_trend.price_change_1d = v_trend.price_change_1d
                        active_trend.price_diff_1d = v_trend.price_diff_1d
                        active_trend.price_change_5d = v_trend.price_change_5d
                        active_trend.price_diff_5d = v_trend.price_diff_5d
                        active_trend.momentum = v_trend.momentum
                        active_trend.volatility = v_trend.volatility
                        active_trend.volume_change = v_trend.volume_change
                        active_trend.rsi = v_trend.rsi
                        active_trend.price_history = v_trend.price_history
                        count += 1
                        continue
                        
                    # Retirement logic for truly new dates
                    active_trend.is_active = False
                    active_trend.valid_to = now
                
                new_trend = MarketTrend(
                    symbol=v_trend.symbol,
                    current_price=v_trend.current_price,
                    market_cap=v_trend.market_cap,
                    pe=v_trend.pe,
                    ps=v_trend.ps,
                    yield_val=v_trend.yield_val,
                    score=v_trend.score,
                    price_change_1d=v_trend.price_change_1d,
                    price_diff_1d=v_trend.price_diff_1d,
                    price_change_5d=v_trend.price_change_5d,
                    price_diff_5d=v_trend.price_diff_5d,
                    momentum=v_trend.momentum,
                    volatility=v_trend.volatility,
                    volume_change=v_trend.volume_change,
                    rsi=v_trend.rsi,
                    market_date=v_trend.market_date,
                    valid_from=now,
                    is_active=True
                )
                session.add(new_trend)
                count += 1
            except Exception as e:
                logger.debug(f"Trend validation skipped for {s.get('symbol')}: {e}")
                
        session.commit()
        logger.info(f"Market Momentum: Synced {count} snapshots to DB.")

    def run_pipeline(self):
        """Full execution flow."""
        logger.info("Starting Market Momentum Analysis with Fundamentals...")
        if not self.config_file.exists():
            logger.error(f"Config file not found: {self.config_file}")
            return
            
        with open(self.config_file, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
            
        stocks_meta = cfg.get('growth_stocks', []) + cfg.get('foundation_stocks', []) + cfg.get('etfs', [])
        symbols = [s['symbol'] for s in stocks_meta]
        meta_map = {s['symbol']: s for s in stocks_meta}
        
        # 1. Fetch Technical Data (Bulk)
        hist_data = self.fetch_data(symbols)
        
        # 2. Fetch Fundamental Data (Parallel)
        fundamentals = self.fetch_fundamentals(symbols)
        
        results = []
        for sym, df in hist_data.items():
            # Merge YAML meta, Live Fundamentals and Technical results
            enriched_meta = meta_map.get(sym, {}).copy()
            enriched_meta.update(fundamentals.get(sym, {}))
            
            res = self.analyze_stock(sym, df, enriched_meta)
            if res: results.append(res)
            
        self.save_to_db(results)
        
        # Save snapshot to JSON for backup
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        logger.info("Pipeline execution complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    
    analyzer = ASXTrendingStocks()
    analyzer.run_pipeline()