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

class ASXTrendingStocks:
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'asx_analyzer.yaml')
        self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.asx_stocks = config.get('stocks', [])
            self.asx_etfs = config.get('etfs', [])
            self.weights = config.get('weights', {
                'price_1d': 0.3, 'price_5d': 0.25, 'price_20d': 0.15,
                'volume_change': 0.2, 'momentum': 0.1
            })
            self.settings = config.get('settings', {
                'period': '1mo', 'min_data_points': 10,
                'rsi_period': 14, 'volatility_window': 252,
                'display_limit': None
            })
            self.thresholds = config.get('thresholds', {
                'rsi_upper': 70, 'rsi_lower': 30,
                'price_change_alert': 5.0, 'volume_change_alert': 50.0
            })
        except Exception as e:
            print(f"Warning: Could not load config file ({e}). Using defaults.")
            self.asx_stocks = []
            self.weights = {}
            self.settings = {}
            self.thresholds = {}
        
    def get_stock_bundle(self, symbol: str, period: str = '1mo') -> tuple:
        """Fetch stock history and metadata info with retry logic"""
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                stock = yf.Ticker(symbol)
                data = stock.history(period=period)
                
                if data.empty:
                     # For valid tickers like ACDC.AX that fail under load, treat empty as a retry-able error
                     raise ValueError("Received empty data")
                     
                info = stock.info
                return data, info
            except Exception as e:
                if attempt < max_retries - 1:
                    sleep_time = base_delay * (2 ** attempt)
                    # print(f"Retry {attempt+1}/{max_retries} for {symbol} after error: {e}")
                    time.sleep(sleep_time)
                else:
                    print(f"Error fetching data for {symbol} after {max_retries} attempts: {e}")
                    return pd.DataFrame(), {}
        return pd.DataFrame(), {}
    
    def calculate_trending_score(self, data: pd.DataFrame) -> Dict:
        """Calculate trending score based on multiple factors"""
        min_points = self.settings.get('min_data_points', 10)
        if data.empty or len(data) < min_points:
            return {'score': 0, 'price_change': 0, 'volume_change': 0, 'momentum': 0}
        
        diff_1d = data['Close'].iloc[-1] - data['Close'].iloc[-2]
        price_1d = (diff_1d / data['Close'].iloc[-2]) * 100
        
        if len(data) > 6:
            diff_5d = data['Close'].iloc[-1] - data['Close'].iloc[-6]
            price_5d = (diff_5d / data['Close'].iloc[-6]) * 100
        else:
            diff_5d = 0
            price_5d = 0
            
        price_20d = ((data['Close'].iloc[-1] - data['Close'].iloc[-21]) / data['Close'].iloc[-21]) * 100 if len(data) > 21 else 0
        
        avg_volume = data['Volume'].mean()
        current_volume = data['Volume'].iloc[-1]
        if avg_volume > 0:
            volume_change = ((current_volume - avg_volume) / avg_volume) * 100
        else:
            volume_change = 0
            
        rsi_period = self.settings.get('rsi_period', 14)
        rsi = self.calculate_rsi(data['Close'], period=rsi_period)
        momentum = (data['Close'].iloc[-1] - data['Close'].iloc[-5]) / data['Close'].iloc[-5] * 100 if len(data) > 5 else 0
        
        returns = data['Close'].pct_change()
        vol_window = self.settings.get('volatility_window', 252)
        volatility = returns.std() * np.sqrt(vol_window) * 100
        
        w = self.weights
        score = (
            price_1d * w.get('price_1d', 0.3) +      
            price_5d * w.get('price_5d', 0.25) +     
            price_20d * w.get('price_20d', 0.15) +   
            volume_change * w.get('volume_change', 0.2) + 
            momentum * w.get('momentum', 0.1)
        )
        
        return {
            'score': round(score, 2),
            'price_change_1d': round(price_1d, 2),
            'price_diff_1d': round(diff_1d, 3),
            'price_change_5d': round(price_5d, 2),
            'price_diff_5d': round(diff_5d, 3),
            'price_change_20d': round(price_20d, 2),
            'volume_change': round(volume_change, 2),
            'momentum': round(momentum, 2),
            'volatility': round(volatility, 2),
            'rsi': round(rsi, 2) if not np.isnan(rsi) else 0
        }
    
    def calculate_annual_return(self, data: pd.DataFrame) -> float:
        """Calculate 1 Year Return"""
        if len(data) < 200: 
            return None
        idx = -252 if len(data) >= 252 else -len(data)
        price_1y_ago = data['Close'].iloc[idx]
        current_price = data['Close'].iloc[-1]
        return ((current_price - price_1y_ago) / price_1y_ago) * 100

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index (RSI) using Wilder's Smoothing"""
        if len(prices) < period:
            return np.nan
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0))
        loss = (-delta.where(delta < 0, 0))
        
        # Wilder's Smoothing (EWM with alpha = 1/period)
        avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    
    def _process_stock(self, stock_info, period, is_etf=False):
        if isinstance(stock_info, dict):
            symbol = stock_info['symbol'].strip()
            industry = stock_info.get('industry', 'Unknown')
            name = stock_info.get('name', 'Unknown')
        else:
            symbol = stock_info.strip()
            industry = 'Unknown'
            name = 'Unknown'
            
        data, info = self.get_stock_bundle(symbol, period=period)
        if not data.empty:
            trending_score = self.calculate_trending_score(data)
            if trending_score['score'] != 0:
                result = {
                    'symbol': symbol,
                    'name': name,
                    'industry': industry,
                    'current_price': round(data['Close'].iloc[-1], 2),
                    'marketCap': info.get('marketCap', None),
                    'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh', None),
                    'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow', None),
                    'pe': info.get('trailingPE', None),
                    'ps': info.get('priceToSalesTrailing12Months', None),
                    'is_etf': is_etf,
                    **trending_score
                }
                
                if is_etf:
                    # Filter out small ETFs (< $500M AUM)
                    t_assets = info.get('totalAssets')
                    if t_assets and t_assets < 500_000_000:
                        return None

                    result['totalAssets'] = t_assets
                    # Yield Fetching with Fallback
                    y_val = info.get('dividendYield')
                    if y_val is None:
                        y_val = info.get('yield')
                    if y_val is None:
                        y_val = info.get('trailingAnnualDividendYield')
                    
                    result['yield'] = y_val
                    result['annual_return'] = self.calculate_annual_return(data)
                    result.pop('ps', None)
                    result['nav'] = info.get('navPrice', None)
                    
                return result
        return None

    def _process_items(self, items_list: List[Dict], is_etf: bool = False) -> List[Dict]:
        period = '1y' if is_etf else self.settings.get('period', '1mo')
        results = []
        unique_items = {}
        for item in items_list:
             if isinstance(item, dict):
                 sym = item['symbol'].strip()
             else:
                 sym = item.strip()
             if sym not in unique_items:
                 unique_items[sym] = item
        
        items_to_process = list(unique_items.values())
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_item = {executor.submit(self._process_stock, item, period, is_etf): item for item in items_to_process}
            for future in concurrent.futures.as_completed(future_to_item):
                try:
                    res = future.result()
                    if res:
                        results.append(res)
                except Exception as exc:
                    print(f"Generated an exception: {exc}")
        return results

    def get_trending_stocks(self) -> Dict[str, List[Dict]]:
        print("Fetching ASX stock data...")
        start_time = time.time()
        
        stock_results = self._process_items(self.asx_stocks, is_etf=False)
        stock_results.sort(key=lambda x: x['score'], reverse=True)
        limit = self.settings.get('display_limit')
        if limit is not None:
            stock_results = stock_results[:limit]
            
        print("Fetching ASX ETF data...")
        etf_results = self._process_items(self.asx_etfs, is_etf=True)
        etf_results.sort(key=lambda x: x['score'], reverse=True)
        if limit is not None:
             etf_results = etf_results[:limit]

        elapsed = time.time() - start_time
        print(f"Data fetching completed in {elapsed:.2f} seconds.\n")
        
        return {
            'stocks': stock_results,
            'etfs': etf_results
        }
    
    def colorize(self, value, metric_type) -> tuple:
        val = float(value)
        colored = ""
        raw = ""
        
        if metric_type == 'rsi':
            if val >= self.thresholds.get('rsi_upper', 70):
                colored = f"{Colors.FAIL}{val:.2f}{Colors.ENDC}"
            elif val <= self.thresholds.get('rsi_lower', 30):
                colored = f"{Colors.GREEN}{val:.2f}{Colors.ENDC}"
            else:
                colored = f"{val:.2f}"
            raw = f"{val:.2f}"
        elif metric_type == 'price_change':
            if val >= self.thresholds.get('price_change_alert', 5.0):
                colored = f"{Colors.GREEN}+{val:.2f}%{Colors.ENDC}"
            elif val <= -self.thresholds.get('price_change_alert', 5.0):
                colored = f"{Colors.FAIL}{val:.2f}%{Colors.ENDC}"
            elif val > 0:
                colored = f"+{val:.2f}%"
            else:
                colored = f"{val:.2f}%"
            if val > 0: raw = f"+{val:.2f}%"
            else: raw = f"{val:.2f}%"
        elif metric_type == 'volume_change':
            if val >= self.thresholds.get('volume_change_alert', 50.0):
                colored = f"{Colors.CYAN}+{val:.2f}%{Colors.ENDC}"
            elif val > 0:
                colored = f"+{val:.2f}%"
            else:
                colored = f"{val:.2f}%"
            if val > 0: raw = f"+{val:.2f}%"
            else: raw = f"{val:.2f}%"
        return colored, len(raw)
        
    def _format_cell(self, text, width, color=None):
        if color:
            if isinstance(text, tuple):
                content, raw_len = text
            else:
                content = f"{color}{text}{Colors.ENDC}"
                raw_len = len(str(text))
        else:
            if isinstance(text, tuple):
                content, raw_len = text
            else:
                content = str(text)
                raw_len = len(str(text))
        padding = max(0, width - raw_len)
        return f"{content}{' ' * padding}"

    def display_section(self, title: str, items: List[Dict], total_analysed: int, is_etf: bool = False):
        if not items:
            print(f"No trending items found for {title}.")
            return

        display_limit = self.settings.get('display_limit')
        limit_desc = f"Top {display_limit}" if display_limit else "All"
        
        print("=" * 195)
        print(f"{Colors.BOLD}{limit_desc} TRENDING {title} (Showing {len(items)} of {total_analysed} analysed){Colors.ENDC}")
        print("=" * 195)

        display_list = list(items)
        display_list.sort(key=lambda x: x['symbol'])
        
        if is_etf:
             cols = [
                ("Symbol", 10), ("Name", 25), ("Category", 22), ("AUM", 10), ("Price", 10), 
                ("PE", 8), ("Yield", 8), 
                ("Score", 8), ("1D %", 15), ("5D %", 15), ("1Y %", 10),
                ("Mom", 10), ("Vol", 10), ("RSI", 8)
            ]
        else:
            cols = [
                ("Symbol", 10), ("Company Name", 25), ("Industry", 22), ("MC", 8), ("Price", 10), 
                ("PE", 8), ("PS", 8), 
                ("Score", 10), ("1D Change", 20), ("5D Change", 20), ("Vol Change", 12), 
                ("Momentum", 12), ("Volatility", 12), ("RSI", 10)
            ]
        
        header_str = ""
        for name, width in cols:
            header_str += f"{name:<{width}} "
        print(header_str)
        print("-" * (sum(c[1] for c in cols) + len(cols)))

        for stock in display_list:
            symbol = (stock['symbol'], len(stock['symbol']))
            raw_name = stock.get('name', 'Unknown')
            if len(raw_name) > 24: raw_name = raw_name[:21] + "..."
            name_cell = (raw_name, len(raw_name))
            
            ind_str = stock.get('industry', 'Unknown')
            if len(ind_str) > 22: ind_str = ind_str[:19] + "..."
            industry = (ind_str, len(ind_str))
            
            if is_etf: mc_val = stock.get('totalAssets')
            else: mc_val = stock.get('marketCap')
                
            if mc_val:
                if mc_val >= 1e9: mc_str = f"${mc_val/1e9:.1f}B"
                else: mc_str = f"${mc_val/1e6:.1f}M"
            else: mc_str = "-"
            
            price = f"${stock['current_price']:.2f}"
            def fmt_nop(val): return f"{val:.2f}" if val is not None else "-"
            pe = fmt_nop(stock.get('pe'))
            
            if is_etf:
                y_val = stock.get('yield')
                if y_val:
                    if y_val < 0.3: ps = f"{y_val*100:.2f}%"
                    else: ps = f"{y_val:.2f}%"
                else: ps = "-"
            else:
                ps = fmt_nop(stock.get('ps'))
            
            score = f"{stock['score']:.2f}"
            v1d, c1d = stock['price_change_1d'], stock['price_diff_1d']
            
            if is_etf:
                t1d = f"{v1d:+.2f}%"
                clr1d = Colors.GREEN if v1d > 0 else (Colors.FAIL if v1d < 0 else "")
                p1d = (f"{clr1d}{t1d}{Colors.ENDC}" if clr1d else t1d, len(t1d))
                v5d, c5d = stock['price_change_5d'], stock['price_diff_5d']
                t5d = f"{v5d:+.2f}%"
                clr5d = Colors.GREEN if v5d > 0 else (Colors.FAIL if v5d < 0 else "")
                p5d = (f"{clr5d}{t5d}{Colors.ENDC}" if clr5d else t5d, len(t5d))
                y1 = stock.get('annual_return')
                if y1 is not None:
                     ty1 = f"{y1:+.1f}%"
                     clry1 = Colors.GREEN if y1 > 0 else (Colors.FAIL if y1 < 0 else "")
                     py1 = (f"{clry1}{ty1}{Colors.ENDC}" if clry1 else ty1, len(ty1))
                else: py1 = ("-", 1)
            else:
                t1d = f"{c1d:+.2f} ({v1d:+.2f}%)"
                clr1d = Colors.GREEN if v1d > 0 else (Colors.FAIL if v1d < 0 else "")
                p1d = (f"{clr1d}{t1d}{Colors.ENDC}" if clr1d else t1d, len(t1d))
                v5d, c5d = stock['price_change_5d'], stock['price_diff_5d']
                t5d = f"{c5d:+.2f} ({v5d:+.2f}%)"
                clr5d = Colors.GREEN if v5d > 0 else (Colors.FAIL if v5d < 0 else "")
                p5d = (f"{clr5d}{t5d}{Colors.ENDC}" if clr5d else t5d, len(t5d))
            
            vol_chg = self.colorize(stock['volume_change'], 'volume_change')
            mom = self.colorize(stock['momentum'], 'price_change') 
            vola = f"{stock['volatility']:.2f}%"
            rsi = self.colorize(stock['rsi'], 'rsi')

            row_str = ""
            row_str += self._format_cell(stock['symbol'], 10, Colors.BOLD) + " "
            row_str += self._format_cell(name_cell, 25) + " "
            row_str += self._format_cell(industry, 22) + " "
            row_str += self._format_cell(mc_str, 10 if is_etf else 8) + " "
            row_str += self._format_cell(price, 10) + " "
            row_str += self._format_cell(pe, 8) + " "
            row_str += self._format_cell(ps, 8) + " "
            row_str += self._format_cell(score, 10 if not is_etf else 8) + " "
            row_str += self._format_cell(p1d, 20 if not is_etf else 15) + " "
            row_str += self._format_cell(p5d, 20 if not is_etf else 15) + " "
            if is_etf: row_str += self._format_cell(py1, 10) + " "
            row_str += self._format_cell(vol_chg if not is_etf else "-", 12) + " "
            row_str += self._format_cell(mom, 12) + " "
            row_str += self._format_cell(vola, 12) + " "
            row_str += self._format_cell(rsi, 10) + " "
            print(row_str)
        print("=" * (sum(c[1] for c in cols) + len(cols)))

    def display_results(self, data: Dict[str, List[Dict]]):
        self.display_section("STOCKS", data.get('stocks', []), len(self.asx_stocks), is_etf=False)
        print("\n")
        self.display_section("ETFs", data.get('etfs', []), len(self.asx_etfs), is_etf=True)

    def _generate_insights_html(self, items: List[Dict], title: str, group_label: str = None) -> str:
        """Generate HTML insights section for a list of items"""
        if not items: return ""
        html = f'<div class="section"><h3>{title} Insights</h3>'
        
        # Original Insights
        top_gainers = sorted(items, key=lambda x: x['price_change_1d'], reverse=True)[:3]
        html += "<h4>Top 3 Gainers (24h)</h4><ul>"
        for s in top_gainers:
            html += f"<li><b>{s['symbol']}</b>: <span class='positive'>{s['price_change_1d']:+.2f}%</span></li>"
        html += "</ul>"
        
        top_losers = sorted(items, key=lambda x: x['price_change_1d'])[:3]
        html += "<h4>Top 3 Decliners (24h)</h4><ul>"
        for s in top_losers:
            html += f"<li><b>{s['symbol']}</b>: <span class='negative'>{s['price_change_1d']:+.2f}%</span></li>"
        html += "</ul>"
        
        # Group Performance (Industry/Category)
        if group_label:
            groups = {}
            for item in items:
                g = item.get('industry', 'Unknown')
                if g not in groups: groups[g] = []
                groups[g].append(item['price_change_1d'])
            
            group_perf = []
            for g_name, changes in groups.items():
                if len(changes) > 0:
                    avg = sum(changes) / len(changes)
                    group_perf.append((g_name, avg))
            
            group_perf.sort(key=lambda x: x[1], reverse=True)
            
            if group_perf:
                html += f"<h4>{group_label} Performance (Avg 1D)</h4><ul>"
                best = group_perf[0]
                worst = group_perf[-1]
                
                b_cls = "positive" if best[1] > 0 else ("negative" if best[1] < 0 else "neutral")
                w_cls = "positive" if worst[1] > 0 else ("negative" if worst[1] < 0 else "neutral")
                
                html += f"<li>Best: <b>{best[0]}</b> (<span class='{b_cls}'>{best[1]:+.2f}%</span>)</li>"
                if len(group_perf) > 1:
                     html += f"<li>Worst: <b>{worst[0]}</b> (<span class='{w_cls}'>{worst[1]:+.2f}%</span>)</li>"
                html += "</ul>"

        sorted_by_vol = sorted(items, key=lambda x: x['volume_change'], reverse=True)
        high_vol = [s for s in sorted_by_vol if s['volume_change'] > 30.0][:3]
        if high_vol:
            html += "<h4>Significant Volume Spikes</h4><ul>"
            for s in high_vol:
                html += f"<li><b>{s['symbol']}</b>: <span class='highlight'>{s['volume_change']:+.2f}%</span> vs avg</li>"
            html += "</ul>"
        
        overbought = sorted([s for s in items if s['rsi'] >= 70], key=lambda x: x['rsi'], reverse=True)
        oversold = sorted([s for s in items if s['rsi'] <= 30], key=lambda x: x['rsi'])
        if overbought or oversold:
            html += "<h4>RSI Alerts</h4>"
            if overbought:
                ob_list = ", ".join([f"<b>{s['symbol']}</b> ({s['rsi']:.1f})" for s in overbought])
                html += f"<p>Overbought (>70): <span class='negative'>{ob_list}</span></p>"
            if oversold:
                os_list = ", ".join([f"<b>{s['symbol']}</b> ({s['rsi']:.1f})" for s in oversold])
                html += f"<p>Oversold (<30): <span class='positive'>{os_list}</span></p>"
        html += "</div>"
        return html

    def generate_html_report(self, data: Dict[str, List[Dict]], save_file: bool = True) -> str:
        date_str = datetime.now().strftime('%Y-%m-%d')
        out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output"))
        os.makedirs(out_dir, exist_ok=True)
        filename = os.path.join(out_dir, "asx_analyzer.html")
        template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "asx_analyzer.html")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        trending_stocks = data.get('stocks', [])
        trending_etfs = data.get('etfs', [])

        def get_color_class(val, type='normal'):
             if val is None: return 'neutral'
             if type == 'rsi':
                 if val >= 70: return 'negative'
                 if val <= 30: return 'positive'
                 return 'neutral'
             if val > 0: return 'positive'
             if val < 0: return 'negative'
             return 'neutral'
             
        def fmt_nop(val): return f"{val:.2f}" if val is not None else "-"

        def fmt_mc(mc_val):
            if mc_val:
                if mc_val >= 1e9: return f"${mc_val/1e9:.1f}B"
                else: return f"${mc_val/1e6:.1f}M"
            return "-"

        # ── Build stock rows ─────────────────────────────────────────────
        stock_rows = ""
        for stock in sorted(trending_stocks, key=lambda x: x['symbol']):
            p1d_class = get_color_class(stock['price_change_1d'])
            p5d_class = get_color_class(stock['price_change_5d'])
            mom_class = get_color_class(stock['momentum'])
            rsi_class = get_color_class(stock['rsi'], 'rsi')
            mc_str = fmt_mc(stock.get('marketCap'))
            
            stock_rows += f"""
            <tr>
                <td><b>{stock['symbol']}</b></td>
                <td>{stock.get('name', 'Unknown')}</td>
                <td>{stock.get('industry', 'Unknown')}</td>
                <td data-sort="{stock.get('marketCap', 0)}">{mc_str}</td>
                <td data-sort="{stock['current_price']}">${stock['current_price']:.2f}</td>
                <td data-sort="{stock.get('pe', -999999)}">{fmt_nop(stock.get('pe'))}</td>
                <td data-sort="{stock.get('ps', -999999)}">{fmt_nop(stock.get('ps'))}</td>
                <td data-sort="{stock['score']}"><span class="score-box">{stock['score']:.2f}</span></td>
                <td class="{p1d_class}" data-sort="{stock['price_change_1d'] or 0}">{stock['price_diff_1d']:+.2f} ({stock['price_change_1d']:+.2f}%)</td>
                <td class="{p5d_class}" data-sort="{stock['price_change_5d'] or 0}">{stock['price_diff_5d']:+.2f} ({stock['price_change_5d']:+.2f}%)</td>
                <td class="{mom_class}" data-sort="{stock['momentum'] or 0}">{stock['momentum']:+.2f}%</td>
                <td data-sort="{stock['volatility'] or 0}">{stock['volatility']:.2f}%</td>
                <td class="{rsi_class}" data-sort="{stock['rsi'] or 0}">{stock['rsi']:.2f}</td>
            </tr>
            """

        # ── Build ETF rows ───────────────────────────────────────────────
        etf_rows = ""
        for stock in sorted(trending_etfs, key=lambda x: x['symbol']):
             p1d_class = get_color_class(stock['price_change_1d'])
             p5d_class = get_color_class(stock['price_change_5d'])
             mom_class = get_color_class(stock['momentum'])
             rsi_class = get_color_class(stock['rsi'], 'rsi')
             y1 = stock.get('annual_return')
             y1_class = get_color_class(y1)
             y1_str = f"{y1:+.2f}%" if y1 is not None else "-"
             mc_str = fmt_mc(stock.get('totalAssets'))
             y_val = stock.get('yield')
             if y_val:
                 if y_val < 0.3: ps = f"{y_val*100:.2f}%"
                 else: ps = f"{y_val:.2f}%"
             else: ps = "-"
             
             etf_rows += f"""
             <tr>
                 <td><b>{stock['symbol']}</b></td>
                 <td>{stock.get('name', 'Unknown')}</td>
                 <td>{stock.get('industry', 'Unknown')}</td>
                 <td data-sort="{stock.get('totalAssets', 0)}">{mc_str}</td>
                 <td data-sort="{stock['current_price']}">${stock['current_price']:.2f}</td>
                 <td data-sort="{stock.get('pe', -999999)}">{fmt_nop(stock.get('pe'))}</td>
                 <td data-sort="{y_val or 0}">{ps}</td>
                 <td data-sort="{stock['score']}"><span class="score-box">{stock['score']:.2f}</span></td>
                 <td class="{p1d_class}" data-sort="{stock['price_change_1d'] or 0}">{stock['price_change_1d']:+.2f}%</td>
                 <td class="{p5d_class}" data-sort="{stock['price_change_5d'] or 0}">{stock['price_change_5d']:+.2f}%</td>
                 <td class="{y1_class}" data-sort="{y1 or 0}">{y1_str}</td>
                 <td class="{mom_class}" data-sort="{stock['momentum'] or 0}">{stock['momentum']:+.2f}%</td>
                 <td data-sort="{stock['volatility'] or 0}">{stock['volatility']:.2f}%</td>
                 <td class="{rsi_class}" data-sort="{stock['rsi'] or 0}">{stock['rsi']:.2f}</td>
             </tr>
             """

        # ── Build insights ───────────────────────────────────────────────
        stock_insights = self._generate_insights_html(trending_stocks, "Stock Market", group_label="Sector")
        etf_insights = self._generate_insights_html(trending_etfs, "ETF Market", group_label="Category")

        # ── Read template and fill placeholders ──────────────────────────
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        html_content = template.replace("{{ timestamp }}", timestamp)
        html_content = html_content.replace("{{ stock_count }}", str(len(trending_stocks)))
        html_content = html_content.replace("{{ etf_count }}", str(len(trending_etfs)))
        html_content = html_content.replace("{{ stock_rows }}", stock_rows)
        html_content = html_content.replace("{{ etf_rows }}", etf_rows)
        html_content = html_content.replace("{{ stock_insights }}", stock_insights)
        html_content = html_content.replace("{{ etf_insights }}", etf_insights)
        
        if save_file:
            try:
                with open(filename, "w", encoding='utf-8') as f:
                    f.write(html_content)
                print(f"\n{Colors.GREEN}Report generated successfully: {filename}{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.FAIL}Failed to generate HTML report: {e}{Colors.ENDC}")
        
        return html_content

def main():
    print("ASX Stocks/ETFs Analyzer")
    print("=" * 50)
    try:
        analyzer = ASXTrendingStocks()
        market_data = analyzer.get_trending_stocks()
        analyzer.display_results(market_data)
        analyzer.generate_html_report(market_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"An error occurred: {e}")
        print("Please check your internet connection and try again.")

if __name__ == "__main__":
    main()