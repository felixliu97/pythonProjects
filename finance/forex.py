import yfinance as yf
import pandas as pd
import pandas_ta as ta
import datetime

def get_real_time_rsi(symbol, interval='1m', period=14):
    # Fetch real-time data
    current_time = datetime.datetime.now()
    start_time = current_time - datetime.timedelta(days=1)  # Get data for the last day
    
    data = yf.download(symbol, start=start_time, end=current_time, interval=interval)
    
    # Calculate RSI
    data['RSI'] = ta.rsi(data['Close'], length=period)
    
    # Get the latest RSI value
    latest_rsi = data['RSI'].iloc[-1]
    
    return latest_rsi

# Get real-time RSI for USD/JPY
symbol = "USDJPY=X"  # Yahoo Finance symbol for USD/JPY
rsi = get_real_time_rsi(symbol)

print(f"Current RSI for USD/JPY: {rsi:.2f}")