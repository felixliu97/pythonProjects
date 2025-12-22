import yfinance as yf
import pandas as pd
import numpy as np
import concurrent.futures
import streamlit as st

# 100 ASX Blue Chip Stocks
ASX_STOCKS = [
    {"symbol": "AGL.AX", "name": "AGL Energy Limited", "industry": "Utilities"},
    {"symbol": "AIA.AX", "name": "Auckland International Airport", "industry": "Industrials"},
    {"symbol": "ALD.AX", "name": "Ampol Limited", "industry": "Energy"},
    {"symbol": "ALL.AX", "name": "Aristocrat Leisure Limited", "industry": "Consumer Cyclical"},
    {"symbol": "ALQ.AX", "name": "ALS Limited", "industry": "Industrials"},
    {"symbol": "ALX.AX", "name": "Atlas Arteria", "industry": "Industrials"},
    {"symbol": "AMC.AX", "name": "Amcor PLC", "industry": "Consumer Cyclical"},
    {"symbol": "ANN.AX", "name": "Ansell Limited", "industry": "Healthcare"},
    {"symbol": "ANZ.AX", "name": "ANZ Group Holdings Limited", "industry": "Financial Services"},
    {"symbol": "APA.AX", "name": "APA Group", "industry": "Utilities"},
    {"symbol": "ARB.AX", "name": "ARB Corporation Limited", "industry": "Consumer Cyclical"},
    {"symbol": "ASX.AX", "name": "ASX Limited", "industry": "Financial Services"},
    {"symbol": "AZJ.AX", "name": "Aurizon Holdings", "industry": "Industrials"},
    {"symbol": "BHP.AX", "name": "BHP Group Limited", "industry": "Basic Materials"},
    {"symbol": "BPT.AX", "name": "Beach Energy", "industry": "Energy"},
    {"symbol": "BRG.AX", "name": "Breville Group", "industry": "Consumer Cyclical"},
    {"symbol": "BSL.AX", "name": "BlueScope Steel", "industry": "Basic Materials"},
    {"symbol": "BXB.AX", "name": "Brambles Limited", "industry": "Industrials"},
    {"symbol": "CAR.AX", "name": "CAR Group Limited", "industry": "Communication Services"},
    {"symbol": "CBA.AX", "name": "Commonwealth Bank of Australia", "industry": "Financial Services"},
    {"symbol": "CGF.AX", "name": "Challenger Limited", "industry": "Financial Services"},
    {"symbol": "CHC.AX", "name": "Charter Hall Group", "industry": "Real Estate"},
    {"symbol": "CNU.AX", "name": "Chorus Limited", "industry": "Communication Services"},
    {"symbol": "COH.AX", "name": "Cochlear Limited", "industry": "Healthcare"},
    {"symbol": "COL.AX", "name": "Coles Group Limited", "industry": "Consumer Defensive"},
    {"symbol": "CPU.AX", "name": "Computershare Limited", "industry": "Financial Services"},
    {"symbol": "CSL.AX", "name": "CSL Limited", "industry": "Healthcare"},
    {"symbol": "CWY.AX", "name": "Cleanaway Waste Management", "industry": "Industrials"},
    {"symbol": "DOW.AX", "name": "Downer EDI", "industry": "Industrials"},
    {"symbol": "DXS.AX", "name": "Dexus", "industry": "Real Estate"},
    {"symbol": "EDV.AX", "name": "Endeavour Group Limited", "industry": "Consumer Defensive"},
    {"symbol": "EVN.AX", "name": "Evolution Mining", "industry": "Basic Materials"},
    {"symbol": "FLT.AX", "name": "Flight Centre Travel Group", "industry": "Consumer Cyclical"},
    {"symbol": "FMG.AX", "name": "Fortescue Ltd", 'industry': 'Basic Materials'},
    {"symbol": "FPH.AX", "name": "Fisher & Paykel Healthcare", "industry": "Healthcare"},
    {"symbol": "GMG.AX", "name": "Goodman Group", "industry": "Real Estate"},
    {"symbol": "GPT.AX", "name": "The GPT Group", "industry": "Real Estate"},
    {"symbol": "HUB.AX", "name": "HUB24 Limited", "industry": "Financial Services"},
    {"symbol": "HVN.AX", "name": "Harvey Norman Holdings", "industry": "Consumer Cyclical"},
    {"symbol": "IAG.AX", "name": "Insurance Australia Group Limited", "industry": "Financial Services"},
    {"symbol": "IGO.AX", "name": "IGO Limited", "industry": "Basic Materials"},
    {"symbol": "JBH.AX", "name": "JB Hi-Fi Limited", "industry": "Consumer Cyclical"},
    {"symbol": "LLC.AX", "name": "Lendlease Group", "industry": "Real Estate"},
    {"symbol": "LYC.AX", "name": "Lynas Rare Earths Limited", "industry": "Basic Materials"},
    {"symbol": "MGR.AX", "name": "Mirvac Group", "industry": "Real Estate"},
    {"symbol": "MIN.AX", "name": "Mineral Resources Limited", "industry": "Basic Materials"},
    {"symbol": "MPL.AX", "name": "Medibank Private Limited", "industry": "Financial Services"},
    {"symbol": "MQG.AX", "name": "Macquarie Group Limited", "industry": "Financial Services"},
    {"symbol": "MTS.AX", "name": "Metcash Limited", "industry": "Consumer Defensive"},
    {"symbol": "NAB.AX", "name": "National Australia Bank Limited", "industry": "Financial Services"},
    {"symbol": "NHC.AX", "name": "New Hope Corporation", "industry": "Energy"},
    {"symbol": "NSR.AX", "name": "National Storage REIT", "industry": "Real Estate"},
    {"symbol": "NST.AX", "name": "Northern Star Resources Limited", "industry": "Basic Materials"},
    {"symbol": "NWL.AX", "name": "Netwealth Group", "industry": 'Financial Services'},
    {"symbol": "NXT.AX", "name": "Nextdc Limited", "industry": "Technology"},
    {"symbol": "ORA.AX", "name": "Orora Limited", "industry": "Consumer Cyclical"},
    {"symbol": "ORG.AX", "name": "Origin Energy Limited", "industry": "Utilities"},
    {"symbol": "ORI.AX", "name": "Orica Limited", "industry": "Basic Materials"},
    {"symbol": "PLS.AX", "name": "Pilbara Minerals Limited", "industry": "Basic Materials"},
    {"symbol": "PME.AX", "name": "Pro Medicus Limited", "industry": "Healthcare"},
    {"symbol": "QAN.AX", "name": "Qantas Airways Limited", "industry": "Industrials"},
    {"symbol": "QBE.AX", "name": "QBE Insurance Group Limited", "industry": "Financial Services"},
    {"symbol": "QUB.AX", "name": "Qube Holdings", "industry": "Industrials"},
    {"symbol": "REA.AX", "name": "REA Group Limited", "industry": "Communication Services"},
    {"symbol": "REH.AX", "name": "Reece Limited", "industry": "Industrials"},
    {"symbol": "RGN.AX", "name": "Region Group", "industry": "Real Estate"},
    {"symbol": "RHC.AX", "name": "Ramsay Health Care Limited", "industry": "Healthcare"},
    {"symbol": "RIO.AX", "name": "Rio Tinto Group", "industry": "Basic Materials"},
    {"symbol": "RMD.AX", "name": "ResMed Inc.", "industry": "Healthcare"},
    {"symbol": "RWC.AX", "name": "Reliance Worldwide Corp", "industry": "Industrials"},
    {"symbol": "S32.AX", "name": "South32 Limited", "industry": "Basic Materials"},
    {"symbol": "SCG.AX", "name": "Scentre Group", "industry": "Real Estate"},
    {"symbol": "SDF.AX", "name": "Steadfast Group", "industry": "Financial Services"},
    {"symbol": "SEK.AX", "name": "SEEK Limited", "industry": "Communication Services"},
    {"symbol": "SFR.AX", "name": "Sandfire Resources", "industry": "Basic Materials"},
    {"symbol": "SGM.AX", "name": "Sims Limited", "industry": "Basic Materials"},
    {"symbol": "SGP.AX", "name": "Stockland", "industry": "Real Estate"},
    {"symbol": "SHL.AX", "name": "Sonic Healthcare Limited", "industry": "Healthcare"},
    {"symbol": "SOL.AX", "name": "Washington H. Soul Pattinson", "industry": "Financial Services"},
    {"symbol": "SPK.AX", "name": "Spark New Zealand", "industry": "Communication Services"},
    {"symbol": "STO.AX", "name": "Santos Limited", "industry": "Energy"},
    {"symbol": "SUL.AX", "name": "Super Retail Group", "industry": "Consumer Cyclical"},
    {"symbol": "SUN.AX", "name": "Suncorp Group Limited", "industry": "Financial Services"},
    {"symbol": "TCL.AX", "name": "Transurban Group", "industry": "Industrials"},
    {"symbol": "TLC.AX", "name": "The Lottery Corporation", "industry": "Consumer Cyclical"},
    {"symbol": "TLS.AX", "name": "Telstra Group Limited", "industry": "Communication Services"},
    {"symbol": "TNE.AX", "name": "Technology One", "industry": "Technology"},
    {"symbol": "TWE.AX", "name": "Treasury Wine Estates Limited", "industry": "Consumer Defensive"},
    {"symbol": "VCX.AX", "name": "Vicinity Centres", "industry": "Real Estate"},
    {"symbol": "VEA.AX", "name": "Viva Energy Group", "industry": "Energy"},
    {"symbol": "VNT.AX", "name": "Ventia Services Group", "industry": "Industrials"},
    {"symbol": "WBC.AX", "name": "Westpac Banking Corporation", "industry": "Financial Services"},
    {"symbol": "WDS.AX", "name": "Woodside Energy Group Ltd", "industry": "Energy"},
    {"symbol": "WES.AX", "name": "Wesfarmers Limited", "industry": "Consumer Cyclical"},
    {"symbol": "WHC.AX", "name": "Whitehaven Coal", "industry": "Energy"},
    {"symbol": "WOR.AX", "name": "Worley Limited", "industry": "Energy"},
    {"symbol": "WOW.AX", "name": "Woolworths Group Limited", "industry": "Consumer Defensive"},
    {"symbol": "WTC.AX", "name": "WiseTech Global Limited", "industry": "Technology"},
    {"symbol": "XRO.AX", "name": "Xero Limited", "industry": "Technology"},
    {"symbol": "YAL.AX", "name": "Yancoal Australia Ltd", "industry": "Energy"}
]

class ASXMonitor:
    def __init__(self):
        self.settings = {
            'rsi_period': 14,
            'volatility_window': 252,
            'weights': {
                'price_1d': 0.3, 'price_5d': 0.25, 'price_20d': 0.15,
                'volume_change': 0.2, 'momentum': 0.1
            }
        }

    def calculate_rsi(self, prices, period=14):
        if len(prices) < period + 1:
            return 50.0
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    def calculate_score(self, data):
        # Simplified scoring logic based on user's previous script
        if data.empty: return 0
        
        diff_1d = data['Close'].iloc[-1] - data['Close'].iloc[-2]
        price_1d = (diff_1d / data['Close'].iloc[-2]) * 100
        
        if len(data) > 6:
            diff_5d = data['Close'].iloc[-1] - data['Close'].iloc[-6]
            price_5d = (diff_5d / data['Close'].iloc[-6]) * 100
        else:
            price_5d = 0
            
        price_20d = ((data['Close'].iloc[-1] - data['Close'].iloc[-21]) / data['Close'].iloc[-21]) * 100 if len(data) > 21 else 0
        
        avg_volume = data['Volume'].mean()
        current_volume = data['Volume'].iloc[-1]
        volume_change = ((current_volume - avg_volume) / avg_volume) * 100 if avg_volume > 0 else 0
        
        momentum = (data['Close'].iloc[-1] - data['Close'].iloc[-5]) / data['Close'].iloc[-5] * 100 if len(data) > 5 else 0
        
        w = self.settings['weights']
        score = (
            price_1d * w['price_1d'] +      
            price_5d * w['price_5d'] +     
            price_20d * w['price_20d'] +   
            volume_change * w['volume_change'] + 
            momentum * w['momentum']
        )
        return round(score, 2)

    def process_stock(self, stock_info):
        symbol = stock_info['symbol']
        try:
            ticker = yf.Ticker(symbol)
            # Fetch 2 months of data to cover all moving averages/RSI
            hist = ticker.history(period="2mo")
            
            if hist.empty:
                return None
                
            info = ticker.info
            
            # Calculations
            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]
            change_1d = ((current_price - prev_close) / prev_close) * 100
            
            if len(hist) > 5:
                close_5d = hist['Close'].iloc[-6]
                change_5d = ((current_price - close_5d) / close_5d) * 100
                momentum = change_5d # Using 5d change as momentum proxy
            else:
                change_5d = 0
                momentum = 0
                
            volatility = hist['Close'].pct_change().std() * np.sqrt(252) * 100
            rsi = self.calculate_rsi(hist['Close'])
            score = self.calculate_score(hist)
            
            return {
                "Symbol": symbol,
                "Name": stock_info['name'],
                "Industry": stock_info['industry'],
                "MC": info.get('marketCap', 0),
                "Price": current_price,
                "PE": info.get('trailingPE', 0),
                "PS": info.get('priceToSalesTrailing12Months', 0),
                "Score": score,
                "1D Change": change_1d,
                "5D Change": change_5d,
                "Momentum": momentum,
                "Volatility": volatility,
                "RSI": rsi
            }
        except Exception as e:
            # print(f"Error fetching {symbol}: {e}")
            return None

# @st.cache_data(ttl=3600)  # Cache data for 1 hour
def fetch_asx_data():
    monitor = ASXMonitor()
    results = []
    
    # Use ThreadPoolExecutor for parallel fetching
    completion_count = 0
    total_stocks = len(ASX_STOCKS)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_stock = {executor.submit(monitor.process_stock, stock): stock for stock in ASX_STOCKS}
        for future in concurrent.futures.as_completed(future_to_stock):
            res = future.result()
            completion_count += 1
            status_text.text(f"Fetching data: {completion_count}/{total_stocks}")
            progress_bar.progress(completion_count / total_stocks)
            
            if res:
                results.append(res)
    
    status_text.empty()
    progress_bar.empty()
                
    df = pd.DataFrame(results)
    if not df.empty:
        # Sort by Score descending
        df = df.sort_values(by="Score", ascending=False)
    return df
