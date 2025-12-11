import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from typing import List, Dict
import warnings
import json
import os
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
        self.config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            self.asx_stocks = config.get('stocks', [])
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
            # Minimal fallback to ensure script runs
            self.asx_stocks = [
                {'symbol': 'BHP.AX', 'industry': 'Basic Materials'},
                {'symbol': 'RIO.AX', 'industry': 'Basic Materials'}, 
                {'symbol': 'CBA.AX', 'industry': 'Financial Services'},
                {'symbol': 'CSL.AX', 'industry': 'Healthcare'},
                {'symbol': 'NAB.AX', 'industry': 'Financial Services'}
            ]
            self.weights = {
                'price_1d': 0.3, 'price_5d': 0.25, 'price_20d': 0.15,
                'volume_change': 0.2, 'momentum': 0.1
            }
            self.settings = {
                'period': '1mo', 'min_data_points': 10,
                'rsi_period': 14, 'volatility_window': 252,
                'display_limit': None
            }
            self.thresholds = {
                'rsi_upper': 70, 'rsi_lower': 30,
                'price_change_alert': 5.0, 'volume_change_alert': 50.0
            }
        
    def get_stock_bundle(self, symbol: str, period: str = '1mo') -> tuple:
        """Fetch stock history and metadata info"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period=period)
            info = stock.info
            return data, info
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame(), {}
    
    def calculate_trending_score(self, data: pd.DataFrame) -> Dict:
        """Calculate trending score based on multiple factors"""
        min_points = self.settings.get('min_data_points', 10)
        if data.empty or len(data) < min_points:
            return {'score': 0, 'price_change': 0, 'volume_change': 0, 'momentum': 0}
        
        # Price change over different periods
        price_1d = ((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
        # Check if we have enough data for 5d and 20d, else use shorter periods or 0
        price_5d = ((data['Close'].iloc[-1] - data['Close'].iloc[-6]) / data['Close'].iloc[-6]) * 100 if len(data) > 6 else 0
        price_20d = ((data['Close'].iloc[-1] - data['Close'].iloc[-21]) / data['Close'].iloc[-21]) * 100 if len(data) > 21 else 0
        
        # Volume analysis
        avg_volume = data['Volume'].mean()
        current_volume = data['Volume'].iloc[-1]
        if avg_volume > 0:
            volume_change = ((current_volume - avg_volume) / avg_volume) * 100
        else:
            volume_change = 0
            
        # Momentum indicators
        rsi_period = self.settings.get('rsi_period', 14)
        rsi = self.calculate_rsi(data['Close'], period=rsi_period)
        momentum = (data['Close'].iloc[-1] - data['Close'].iloc[-5]) / data['Close'].iloc[-5] * 100 if len(data) > 5 else 0
        
        # Volatility
        returns = data['Close'].pct_change()
        vol_window = self.settings.get('volatility_window', 252)
        volatility = returns.std() * np.sqrt(vol_window) * 100
        
        # Calculate composite score
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
            'price_change_5d': round(price_5d, 2),
            'price_change_20d': round(price_20d, 2),
            'volume_change': round(volume_change, 2),
            'momentum': round(momentum, 2),
            'volatility': round(volatility, 2),
            'rsi': round(rsi, 2) if not np.isnan(rsi) else 0
        }
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return np.nan
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    
    def get_trending_stocks(self, top_n: int = None) -> List[Dict]:
        """Get trending stocks"""
        print("Fetching ASX stock data and calculating trending scores...")
        print("This may take a few minutes...\n")
        
        trending_data = []
        
        period = self.settings.get('period', '1mo')
        processed_symbols = set()
        for stock_info in self.asx_stocks:
            # Handle both dict (new config) and string (legacy/fallback)
            if isinstance(stock_info, dict):
                symbol = stock_info['symbol'].strip()
                industry = stock_info.get('industry', 'Unknown')
                name = stock_info.get('name', 'Unknown')
            else:
                symbol = stock_info.strip()
                industry = 'Unknown'
                name = 'Unknown'
                
            if symbol in processed_symbols:
                continue
            processed_symbols.add(symbol)
                
            data, info = self.get_stock_bundle(symbol, period=period)
            if not data.empty:
                trending_score = self.calculate_trending_score(data)
                if trending_score['score'] != 0:
                    trending_data.append({
                        'symbol': symbol,
                        'name': name,
                        'industry': industry,
                        'current_price': round(data['Close'].iloc[-1], 2),
                        'pe': info.get('trailingPE', None),
                        'ps': info.get('priceToSalesTrailing12Months', None),
                        **trending_score
                    })
        
        # Sort by trending score
        trending_data.sort(key=lambda x: x['score'], reverse=True)
        
        # FAIL-SAFE DEDUPLICATION: Ensure absolutely no duplicates by symbol
        unique_map = {}
        for item in trending_data:
            unique_map[item['symbol']] = item
        trending_data = list(unique_map.values())
        
        # Apply limit if configured
        limit = self.settings.get('display_limit')
        if limit is not None:
            return trending_data[:limit]
        return trending_data
    
    def colorize(self, value, metric_type) -> tuple:
        """Apply colors based on thresholds. Returns (colored_str, raw_len)"""
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
                
            if val > 0:
                raw = f"+{val:.2f}%"
            else:
                raw = f"{val:.2f}%"

        elif metric_type == 'volume_change':
            if val >= self.thresholds.get('volume_change_alert', 50.0):
                colored = f"{Colors.CYAN}+{val:.2f}%{Colors.ENDC}"
            elif val > 0:
                colored = f"+{val:.2f}%"
            else:
                colored = f"{val:.2f}%"
                
            if val > 0:
                raw = f"+{val:.2f}%"
            else:
                raw = f"{val:.2f}%"
                
        return colored, len(raw)
        
    def _format_cell(self, text, width, color=None):
        """Helper to format cell with correct padding regardless of ANSI codes"""
        if color:
             # If it's a tuple from colorize, unzip it
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

    def display_results(self, trending_stocks: List[Dict]):
        """Display trending stocks in a formatted table"""
        if not trending_stocks:
            print("No trending stocks found.")
            return
        
        # Check config for display limit
        display_limit = self.settings.get('display_limit')
        limit_desc = f"Top {display_limit}" if display_limit else "All"
        
        print("=" * 195)
        # Dynamic title based on count
        title = f"{Colors.BOLD}{limit_desc} TRENDING STOCKS ON ASX (Showing {len(trending_stocks)} of {len(self.asx_stocks)} analysed){Colors.ENDC}"
        print(title)
        print("=" * 195)
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 195)
        
        # Sort by Symbol
        trending_stocks.sort(key=lambda x: x['symbol'])
        
        # Header
        # Define columns and widths
        cols = [
            ("Symbol", 10), ("Company Name", 25), ("Industry", 22), ("Price", 10), 
            ("PE", 8), ("PS", 8), 
            ("Score", 10), ("1D Change", 12), ("5D Change", 12), ("Vol Change", 12), 
            ("Momentum", 12), ("Volatility", 12), ("RSI", 10)
        ]
        
        header_str = ""
        for name, width in cols:
            header_str += f"{name:<{width}} "
        print(header_str)
        print("-" * 195)

        for stock in trending_stocks:
            # Prepare row data
            symbol = (stock['symbol'], len(stock['symbol']))
            
            # Truncate company name if too long
            raw_name = stock.get('name', 'Unknown')
            if len(raw_name) > 24:
                raw_name = raw_name[:21] + "..."
            name_cell = (raw_name, len(raw_name))
            
            industry = (stock.get('industry', 'Unknown'), len(stock.get('industry', 'Unknown')))
            price = f"${stock['current_price']:.2f}"
            
            # Financials with check
            def fmt_nop(val): return f"{val:.2f}" if val is not None else "-"
            pe = fmt_nop(stock.get('pe'))
            ps = fmt_nop(stock.get('ps'))
            
            score = f"{stock['score']:.2f}"
            
            p1d = self.colorize(stock['price_change_1d'], 'price_change')
            p5d = self.colorize(stock['price_change_5d'], 'price_change')
            vol_chg = self.colorize(stock['volume_change'], 'volume_change')
            mom = self.colorize(stock['momentum'], 'price_change') 
            vola = f"{stock['volatility']:.2f}%"
            
            # RSI logic
            rsi_val = stock['rsi']
            rsi = self.colorize(rsi_val, 'rsi')

            row_str = ""
            # Symbol
            row_str += self._format_cell(stock['symbol'], 10, Colors.BOLD) + " "
            # Company Name
            row_str += self._format_cell(name_cell, 25) + " "
            # Industry
            row_str += self._format_cell(stock.get('industry', 'Unknown'), 22) + " "
            # Price
            row_str += self._format_cell(price, 10) + " "
            # Financials
            row_str += self._format_cell(pe, 8) + " "
            row_str += self._format_cell(ps, 8) + " "
            # Score
            row_str += self._format_cell(score, 10) + " "
            # 1D
            row_str += self._format_cell(p1d, 12) + " "
            # 5D
            row_str += self._format_cell(p5d, 12) + " "
            # Vol
            row_str += self._format_cell(vol_chg, 12) + " "
            # Mom
            row_str += self._format_cell(mom, 12) + " "
            # Volatility
            row_str += self._format_cell(vola, 12) + " "
            # RSI
            row_str += self._format_cell(rsi, 10) + " "
            
            print(row_str)

        print("=" * 195)
        
        # Additional insights
        print("\nMARKET INSIGHTS:")
        print("-" * 50)
        
        # 1. Top Gainers & Losers
        sorted_by_change = sorted(trending_stocks, key=lambda x: x['price_change_1d'], reverse=True)
        top_gainers = sorted_by_change[:3]
        top_losers = sorted_by_change[-3:]
        
        print(f"{Colors.BOLD}Top 3 Gainers (24h):{Colors.ENDC}")
        for s in top_gainers:
            change = s['price_change_1d']
            color = Colors.GREEN if change > 0 else Colors.FAIL
            print(f"  {s['symbol']} ({s.get('name', 'Unknown')[:20]}): {color}{change:+.2f}%{Colors.ENDC}")
            
        print(f"\n{Colors.BOLD}Top 3 Decliners (24h):{Colors.ENDC}")
        for s in reversed(top_losers):
            change = s['price_change_1d']
            color = Colors.GREEN if change > 0 else Colors.FAIL
            print(f"  {s['symbol']} ({s.get('name', 'Unknown')[:20]}): {color}{change:+.2f}%{Colors.ENDC}")
            
        # 2. Volume Spikes
        sorted_by_vol = sorted(trending_stocks, key=lambda x: x['volume_change'], reverse=True)
        high_vol = [s for s in sorted_by_vol if s['volume_change'] > 30.0][:3]
        
        if high_vol:
            print(f"\n{Colors.BOLD}Significant Volume Spikes:{Colors.ENDC}")
            for s in high_vol:
                print(f"  {s['symbol']}: {Colors.CYAN}{s['volume_change']:+.2f}%{Colors.ENDC} vs avg")
                
        # 3. RSI Extremes
        overbought = [s for s in trending_stocks if s['rsi'] >= 70]
        oversold = [s for s in trending_stocks if s['rsi'] <= 30]
        
        if overbought or oversold:
            print(f"\n{Colors.BOLD}RSI Alerts:{Colors.ENDC}")
            if overbought:
                ob_list = [f"{Colors.FAIL}{s['symbol']} ({s['rsi']:.1f}){Colors.ENDC}" for s in overbought]
                print(f"  Overbought (>70): {', '.join(ob_list)}")
            if oversold:
                os_list = [f"{Colors.GREEN}{s['symbol']} ({s['rsi']:.1f}){Colors.ENDC}" for s in oversold]
                print(f"  Oversold (<30):   {', '.join(os_list)}")

        # 4. Top Ranked (Corrected logic)
        print(f"\n{Colors.BOLD}HIGHEST TRENDING SCORE:{Colors.ENDC}")
        best_stock = max(trending_stocks, key=lambda x: x['score'])
        print(f"  {best_stock['symbol']} ({best_stock.get('name', 'Unknown')}): {best_stock['score']}")
        if best_stock['score'] < 0:
            print(f"  {Colors.WARNING}Note: Even the top stock has a negative score, indicating generally weak market momentum.{Colors.ENDC}")

        print("\n" + "=" * 50)

def main():
    """Main function to run the ASX trending stocks analysis"""
    print("ASX Trending Stocks Analyzer")
    print("=" * 50)
    
    try:
        # Initialize the analyzer
        analyzer = ASXTrendingStocks()
        
        # Get trending stocks (limit handled by config)
        trending_stocks = analyzer.get_trending_stocks()
        
        # Display results
        analyzer.display_results(trending_stocks)
        
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please check your internet connection and try again.")

if __name__ == "__main__":
    main() 