import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from typing import List, Dict
import warnings
import yaml
import os
import concurrent.futures
import time
import io
import json
import re
import sys
import argparse
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

warnings.filterwarnings('ignore')

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DIM = '\033[2m'

    @staticmethod
    def ok(msg):    print(f"{Colors.GREEN}{msg}{Colors.ENDC}")
    @staticmethod
    def warn(msg):  print(f"{Colors.WARNING}{msg}{Colors.ENDC}")
    @staticmethod
    def fail(msg):  print(f"{Colors.FAIL}{Colors.BOLD}{msg}{Colors.ENDC}")
    @staticmethod
    def info(msg):  print(f"{Colors.DIM}{msg}{Colors.ENDC}")

class ASXTrendingStocks:
    def __init__(self):
        # Use absolute paths for stability
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_dir = os.path.join(self.root_dir, 'config')
        self.config_file = os.path.join(self.config_dir, 'asx_analyzer.yaml')
        self.output_dir = os.path.join(self.root_dir, 'output')
        
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.load_global_settings()
        self.load_config()

    def load_global_settings(self):
        settings_path = os.path.join(self.config_dir, 'settings.yaml')
        self.global_settings = {}
        if os.path.exists(settings_path):
            with open(settings_path, 'r', encoding='utf-8') as f:
                self.global_settings = yaml.safe_load(f)

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            else:
                config = {}
            
            # Merge with global settings if available
            g_analyzer = self.global_settings.get('analyzer', {})
                
            self.growth_stocks = config.get('growth_stocks', [])
            self.foundation_stocks = config.get('foundation_stocks', [])
            self.asx_etfs = config.get('etfs', [])
            self.weights = config.get('weights') or g_analyzer.get('weights') or {
                'price_1d': 0.3, 'price_5d': 0.25, 'price_20d': 0.15,
                'volume_change': 0.2, 'momentum': 0.1
            }
            self.settings = config.get('settings', {
                'period': '1mo', 'min_data_points': 10,
                'rsi_period': 14, 'volatility_window': 252,
                'display_limit': None
            })
            self.thresholds = config.get('thresholds') or g_analyzer.get('thresholds') or {
                'rsi_upper': 70, 'rsi_lower': 30,
                'price_change_alert': 5.0, 'volume_change_alert': 50.0
            }
            self.cache_ttl = g_analyzer.get('cache_ttl_minutes', 10)
            self.cache_file = os.path.join(self.output_dir, 'asx_analyzer.json')
        except Exception as e:
            Colors.warn(f"Warning: Could not load config file ({e}). Using defaults.")
            self.growth_stocks = []
            self.foundation_stocks = []
            self.asx_etfs = []
            self.weights = {}
            self.settings = {}
            self.thresholds = {}

    def get_stock_bundle(self, symbol: str, period: str = '1mo') -> tuple:
        """Fetch stock history and metadata info with retry logic"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                stock = yf.Ticker(symbol)
                data = stock.history(period=period)
                if data.empty:
                     raise ValueError("Empty data returned")
                info = stock.info
                return data, info
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(1)
        return pd.DataFrame(), {}
    
    def calculate_rsi(self, prices, period=14):
        if len(prices) < period + 1: return 50.0
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not np.isnan(rsi.iloc[-1]) else 50.0

    def generate_sparkline(self, data: pd.Series):
        if data.empty: return ""
        if not HAS_MATPLOTLIB:
            # Simple text-based sparkline fallback
            try:
                vals = data.values
                if len(vals) < 2: return ""
                diff = vals[-1] - vals[0]
                return f'<span style="color:{"#10b981" if diff > 0 else "#ef4444"}">{"↗" if diff > 0 else "↘"}</span>'
            except: return ""
            
        try:
            plt.figure(figsize=(1.5, 0.4))
            plt.plot(data.values, color='#3b82f6', linewidth=2)
            plt.axis('off')
            plt.tight_layout(pad=0)
            
            buf = io.BytesIO()
            plt.savefig(buf, format='svg', transparent=True)
            plt.close()
            buf.seek(0)
            return buf.getvalue().decode('utf-8')
        except Exception:
            return ""

    def calculate_trending_score(self, data: pd.DataFrame) -> Dict:
        """Calculate trending score based on multiple factors"""
        min_points = self.settings.get('min_data_points', 10)
        if data.empty or len(data) < 2:
            return {'score': 0, 'price_change_1d': 0, 'price_diff_1d': 0, 'rsi': 50}
        
        last_price = data['Close'].iloc[-1]
        prev_price = data['Close'].iloc[-2]
        
        diff_1d = last_price - prev_price
        price_1d = (diff_1d / prev_price) * 100 if prev_price != 0 else 0
        
        price_5d = ((last_price - data['Close'].iloc[-6]) / data['Close'].iloc[-6]) * 100 if len(data) >= 6 else 0
        price_20d = ((last_price - data['Close'].iloc[-21]) / data['Close'].iloc[-21]) * 100 if len(data) >= 21 else 0
        
        avg_vol = data['Volume'].mean()
        vol_change = ((data['Volume'].iloc[-1] - avg_vol) / avg_vol) * 100 if avg_vol > 0 else 0
        score_vol_change = min(vol_change, 400.0)
        
        rsi = self.calculate_rsi(data['Close'], self.settings.get('rsi_period', 14))
        momentum = (rsi - 50)
        
        volatility = data['Close'].pct_change().std() * np.sqrt(252) * 100
        
        w = self.weights
        score = (
            price_1d * w.get('price_1d', 0.3) +      
            price_5d * w.get('price_5d', 0.25) +     
            price_20d * w.get('price_20d', 0.15) +   
            score_vol_change * w.get('volume_change', 0.2) + 
            momentum * w.get('momentum', 0.1)
        )
        
        return {
            'score': round(float(score), 2),
            'price_change_1d': round(float(price_1d), 3),
            'price_diff_1d': round(float(diff_1d), 3),
            'price_change_5d': round(float(price_5d), 3),
            'price_diff_5d': round(float(last_price - data['Close'].iloc[-6]), 3) if len(data) >= 6 else 0,
            'price_change_20d': round(float(price_20d), 3),
            'volume_change': round(float(vol_change), 2),
            'momentum': round(float(momentum), 2),
            'volatility': round(float(volatility), 2) if not np.isnan(volatility) else 0,
            'rsi': round(float(rsi), 2),
            'sparkline': self.generate_sparkline(data['Close'][-20:] if len(data) >= 20 else data['Close'])
        }

    def _process_stock(self, config_item, is_etf=False):
        symbol = config_item['symbol'] if isinstance(config_item, dict) else config_item
        # Colors.info(f"Processing {symbol}...")
        
        data, info = self.get_stock_bundle(symbol)
        if data.empty: return None
        
        metrics = self.calculate_trending_score(data)
        
        # Metadata fallbacks
        name = config_item.get('name') if isinstance(config_item, dict) else None
        if not name:
            name = info.get('longName') or info.get('shortName') or symbol
            
        industry = config_item.get('industry') if isinstance(config_item, dict) else None
        if not industry:
            industry = info.get('industry') or info.get('sector') or ("ETF" if is_etf else "Unknown")
            
        mc = info.get('marketCap') or info.get('totalAssets') or 0
        pe = info.get('trailingPE') or info.get('forwardPE') or 0
        ps = info.get('priceToSalesTrailing12Months') or 0
        raw_yield = info.get('yield') or info.get('dividendYield') or 0
        # yfinance can return yield as decimal (0.04) or percentage (4.0)
        dy = raw_yield * 100 if raw_yield < 1.0 else raw_yield
        
        # Stability fix: handle infinity/NaN which can break JSON/Template rendering
        if pe == float('inf') or pe == float('-inf') or (isinstance(pe, float) and np.isnan(pe)): pe = 0
        if ps == float('inf') or ps == float('-inf') or (isinstance(ps, float) and np.isnan(ps)): ps = 0
        
        res = {
            'symbol': symbol,
            'name': name,
            'industry': industry,
            'marketCap': mc,
            'pe': pe,
            'ps': ps,
            'yield': round(float(dy), 2),
            'is_etf': is_etf,
            'current_price': round(float(data['Close'].iloc[-1]), 4),
        }
        res.update(metrics)
        return res

    def get_trending_stocks(self):
        print(f"\n{Colors.BOLD}{Colors.CYAN}Analysing Market Momentum...{Colors.ENDC}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            growth_futures = [executor.submit(self._process_stock, s) for s in self.growth_stocks]
            found_futures = [executor.submit(self._process_stock, s) for s in self.foundation_stocks]
            etf_futures = [executor.submit(self._process_stock, e, True) for e in self.asx_etfs]
            
            growth_results = [f.result() for f in concurrent.futures.as_completed(growth_futures) if f.result()]
            foundation_results = [f.result() for f in concurrent.futures.as_completed(found_futures) if f.result()]
            etf_results = [f.result() for f in concurrent.futures.as_completed(etf_futures) if f.result()]
            
        growth_results.sort(key=lambda x: x['score'], reverse=True)
        foundation_results.sort(key=lambda x: x['score'], reverse=True)
        etf_results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'growth_stocks': growth_results,
            'foundation_stocks': foundation_results,
            'etfs': etf_results,
            'global_timeline': self.get_global_timeline(),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def get_global_timeline(self):
        """Aggregate all FUTURE key catalysts from asx_catalysts.yaml and sort them"""
        catalysts_path = os.path.join(self.config_dir, 'asx_catalysts.yaml')
        if not os.path.exists(catalysts_path):
            return []
            
        try:
            with open(catalysts_path, 'r', encoding='utf-8') as f:
                stocks = yaml.safe_load(f)
            if not stocks: return []
            
            all_events = []
            for s in stocks:
                ticker = s.get('Ticker', '???')
                catalysts = s.get('Catalysts', [])
                for cat_text in catalysts:
                    # Extract a display time label (e.g., "2026 4月")
                    match = re.search(r'(\d{4})[年/\s]?(\d{1,2}月|[QqHh][1-4]|年中|年底|下旬|上旬)', cat_text)
                    time_label = match.group(0) if match else "Future"
                    
                    # Sort logic: approximate date
                    sort_date = self._approximate_date(cat_text)
                    
                    all_events.append({
                        'ticker': ticker,
                        'time': time_label,
                        'event': cat_text,
                        'sort_key': sort_date
                    })
            
            # Sort by date
            all_events.sort(key=lambda x: x['sort_key'])
            
            # Filter out past events (keep current day and future)
            cutoff = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d') # Small buffer
            return [e for e in all_events if e['sort_key'] >= cutoff]
            
        except Exception as e:
            Colors.warn(f"Error aggregating global timeline: {e}")
            return []

    def _approximate_date(self, label):
        """Convert vague time labels to sortable YYYY-MM-DD strings"""
        label = label.lower().strip()
        
        # Standard YYYY-MM-DD
        if re.search(r'\d{4}-\d{2}-\d{2}', label):
            m = re.search(r'\d{4}-\d{2}-\d{2}', label)
            return m.group(0)
        
        # YYYY-MM
        if re.search(r'\d{4}-\d{2}', label):
            m = re.search(r'\d{4}-\d{2}', label)
            return f"{m.group(0)}-28"
            
        # Quarter/Half/Year
        match_year = re.search(r'(\d{4})', label)
        year = match_year.group(1) if match_year else "2026"
        
        # Chinese Month: "4月"
        match_month = re.search(r'(\d{1,2})月', label)
        if match_month:
            month = int(match_month.group(1))
            return f"{year}-{month:02d}-15"

        if 'q1' in label: return f"{year}-02-15"
        if 'q2' in label: return f"{year}-05-15"
        if 'q3' in label: return f"{year}-08-15"
        if 'q4' in label: return f"{year}-11-15"
        if 'h1' in label: return f"{year}-03-15"
        if 'h2' in label: return f"{year}-09-15"
        if '年中' in label: return f"{year}-06-15"
        if '年底' in label: return f"{year}-12-15"
        
        return f"{year}-12-31" # Default to end of year if unknown

    def _convert_to_python_types(self, obj):
        if isinstance(obj, dict):
            return {k: self._convert_to_python_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_python_types(i) for i in obj]
        elif hasattr(obj, 'item'): 
            return obj.item()
        elif isinstance(obj, np.generic):
            return obj.tolist()
        return obj

    def save_results(self, data):
        output_file = os.path.join(self.output_dir, 'asx_analyzer.json')
        # Filter sparkline out for JSON/YAML to keep them clean
        clean_data = self._convert_to_python_types(data)
        
        # Remove sparkline from JSON data to save space, but it's already generated for HTML if needed
        # In this unified version, we keep the data clean.
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(clean_data, f, indent=2, ensure_ascii=False)
        
        # self._write_compact_config(clean_data) # Optional: update config
        Colors.ok(f"Saved results to {output_file}")

    def _write_compact_config(self, config):
        """Write a readable YAML config for the next run"""
        lines = ["settings:", "  period: 1mo", "  min_data_points: 10", f"  display_limit: {self.settings.get('display_limit', 'null')}", ""]
        
        def flow(d):
            return '{' + f"symbol: {d.get('symbol')}, name: \"{d.get('name')}\", industry: \"{d.get('industry')}\", score: {d.get('score')}" + '}'

        lines.append("stocks:")
        for s in config.get('stocks', []):
            lines.append(f"  - {flow(s)}")
            
        lines.append("\netfs:")
        for e in config.get('etfs', []):
            lines.append(f"  - {flow(e)}")

        with open(self.config_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Bypass cache")
    args = parser.parse_args()

    # Cache Check
    analyzer = ASXTrendingStocks()
    if not args.force and os.path.exists(analyzer.cache_file):
        mtime = os.path.getmtime(analyzer.cache_file)
        elapsed = (time.time() - mtime) / 60
        if elapsed < analyzer.cache_ttl:
            from datetime import datetime
            print(f"Using cached results ({round(elapsed, 1)} min ago). Use --force to refresh.")
            sys.exit(0)

    market_data = analyzer.get_trending_stocks()
    analyzer.save_results(market_data)