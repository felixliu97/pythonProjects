import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from typing import List, Dict
import warnings
warnings.filterwarnings('ignore')

class ASXTrendingStocks:
    def __init__(self):
        self.asx_stocks = [
            'BHP.AX', 'RIO.AX', 'CBA.AX', 'CSL.AX', 'NAB.AX', 'ANZ.AX', 'WBC.AX', 'MQG.AX',
            'WES.AX', 'WOW.AX', 'TLS.AX', 'TCL.AX', 'QBE.AX', 'IAG.AX', 'SUN.AX', 'AMP.AX',
            'ORG.AX', 'AGL.AX', 'STO.AX', 'WPL.AX', 'BXB.AX', 'REA.AX', 'CAR.AX', 'APX.AX',
            'NCM.AX', 'NST.AX', 'EVN.AX', 'RRL.AX', 'MIN.AX', 'IGO.AX', 'LYC.AX', 'PLS.AX',
            'FMG.AX', 'FMG.AX', 'BHP.AX', 'RIO.AX', 'FMG.AX', 'NCM.AX', 'NST.AX', 'EVN.AX',
            'RRL.AX', 'MIN.AX', 'IGO.AX', 'LYC.AX', 'PLS.AX', 'FMG.AX', 'FMG.AX', 'BHP.AX'
        ]
        
    def get_stock_data(self, symbol: str, period: str = '1mo') -> pd.DataFrame:
        """Fetch stock data for a given symbol"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period=period)
            return data
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_trending_score(self, data: pd.DataFrame) -> Dict:
        """Calculate trending score based on multiple factors"""
        if data.empty or len(data) < 10:
            return {'score': 0, 'price_change': 0, 'volume_change': 0, 'momentum': 0}
        
        # Price change over different periods
        price_1d = ((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
        price_5d = ((data['Close'].iloc[-1] - data['Close'].iloc[-6]) / data['Close'].iloc[-6]) * 100
        price_20d = ((data['Close'].iloc[-1] - data['Close'].iloc[-21]) / data['Close'].iloc[-21]) * 100
        
        # Volume analysis
        avg_volume = data['Volume'].mean()
        current_volume = data['Volume'].iloc[-1]
        volume_change = ((current_volume - avg_volume) / avg_volume) * 100
        
        # Momentum indicators
        rsi = self.calculate_rsi(data['Close'])
        momentum = (data['Close'].iloc[-1] - data['Close'].iloc[-5]) / data['Close'].iloc[-5] * 100
        
        # Volatility
        returns = data['Close'].pct_change()
        volatility = returns.std() * np.sqrt(252) * 100
        
        # Calculate composite score
        score = (
            price_1d * 0.3 +      # 1-day price change (30% weight)
            price_5d * 0.25 +     # 5-day price change (25% weight)
            price_20d * 0.15 +    # 20-day price change (15% weight)
            volume_change * 0.2 +  # Volume change (20% weight)
            momentum * 0.1         # Momentum (10% weight)
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
    
    def get_trending_stocks(self, top_n: int = 10) -> List[Dict]:
        """Get top trending stocks"""
        print("Fetching ASX stock data and calculating trending scores...")
        print("This may take a few minutes...\n")
        
        trending_data = []
        
        for symbol in self.asx_stocks:
            data = self.get_stock_data(symbol)
            if not data.empty:
                trending_score = self.calculate_trending_score(data)
                if trending_score['score'] != 0:
                    trending_data.append({
                        'symbol': symbol,
                        'current_price': round(data['Close'].iloc[-1], 2),
                        **trending_score
                    })
        
        # Sort by trending score and get top N
        trending_data.sort(key=lambda x: x['score'], reverse=True)
        return trending_data[:top_n]
    
    def display_results(self, trending_stocks: List[Dict]):
        """Display trending stocks in a formatted table"""
        if not trending_stocks:
            print("No trending stocks found.")
            return
        
        print("=" * 120)
        print("TOP 10 TRENDING STOCKS ON ASX")
        print("=" * 120)
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 120)
        
        # Create DataFrame for better display
        df = pd.DataFrame(trending_stocks)
        df = df[['symbol', 'current_price', 'score', 'price_change_1d', 'price_change_5d', 
                 'volume_change', 'momentum', 'volatility', 'rsi']]
        
        # Rename columns for better readability
        df.columns = ['Symbol', 'Price', 'Trend Score', '1D Change%', '5D Change%', 
                     'Volume Change%', 'Momentum%', 'Volatility%', 'RSI']
        
        # Format percentage columns
        percentage_cols = ['1D Change%', '5D Change%', 'Volume Change%', 'Momentum%', 'Volatility%']
        for col in percentage_cols:
            df[col] = df[col].apply(lambda x: f"{x:+.2f}%" if x != 0 else "0.00%")
        
        # Display the table
        print(df.to_string(index=False))
        print("\n" + "=" * 120)
        
        # Additional insights
        print("\nKEY INSIGHTS:")
        print("- Trend Score: Composite score based on price changes, volume, and momentum")
        print("- 1D/5D Change: Percentage change over 1 and 5 trading days")
        print("- Volume Change: Current volume compared to average volume")
        print("- Momentum: 5-day price momentum")
        print("- Volatility: Annualized volatility")
        print("- RSI: Relative Strength Index (overbought > 70, oversold < 30)")
        
        # Top performers summary
        print(f"\nTOP PERFORMERS:")
        print(f"Best 1-day gainer: {trending_stocks[0]['symbol']} ({trending_stocks[0]['price_change_1d']:+.2f}%)")
        print(f"Best 5-day gainer: {max(trending_stocks, key=lambda x: x['price_change_5d'])['symbol']} ({max(trending_stocks, key=lambda x: x['price_change_5d'])['price_change_5d']:+.2f}%)")
        print(f"Highest volume surge: {max(trending_stocks, key=lambda x: x['volume_change'])['symbol']} ({max(trending_stocks, key=lambda x: x['volume_change'])['volume_change']:+.2f}%)")

def main():
    """Main function to run the ASX trending stocks analysis"""
    print("ASX Trending Stocks Analyzer")
    print("=" * 50)
    
    try:
        # Initialize the analyzer
        analyzer = ASXTrendingStocks()
        
        # Get trending stocks
        trending_stocks = analyzer.get_trending_stocks(top_n=10)
        
        # Display results
        analyzer.display_results(trending_stocks)
        
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please check your internet connection and try again.")

if __name__ == "__main__":
    main() 