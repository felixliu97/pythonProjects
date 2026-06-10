import argparse
import csv
import yfinance as yf

try:
    from utils import get_root_dir, logger, ticker_clean
except ImportError:
    from scripts.utils import get_root_dir, logger, ticker_clean

def fetch_and_export(tickers: str, filename: str = "recent_stock_data.csv"):
    ticker_list = [ticker_clean(t) for t in tickers.replace('，', ',').split(",") if t.strip()]
    if not ticker_list:
        logger.error("No valid tickers provided.")
        return

    out_dir = get_root_dir() / "output"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / filename
    
    rows = []
    logger.info(f"Fetching data for {len(ticker_list)} tickers: {', '.join(ticker_list)}")
    
    for t in ticker_list:
        try:
            asx_sym = f"{t}.AX"
            ticker = yf.Ticker(asx_sym)
            hist = ticker.history(period="5d")
            
            if hist.empty or len(hist) < 2:
                logger.warning(f"Not enough data for {t}")
                continue
                
            today_data = hist.iloc[-1]
            yesterday_data = hist.iloc[-2]
            
            today_date = hist.index[-1].strftime("%Y-%m-%d")
            yesterday_date = hist.index[-2].strftime("%Y-%m-%d")
            
            today_open = round(today_data["Open"], 4)
            today_high = round(today_data["High"], 4)
            today_low = round(today_data["Low"], 4)
            today_close = round(today_data["Close"], 4)
            today_vol = int(today_data["Volume"])
            
            yesterday_open = round(yesterday_data["Open"], 4)
            yesterday_high = round(yesterday_data["High"], 4)
            yesterday_low = round(yesterday_data["Low"], 4)
            yesterday_close = round(yesterday_data["Close"], 4)
            yesterday_vol = int(yesterday_data["Volume"])
            
            today_change = round((today_close - yesterday_close) / yesterday_close * 100, 2)
            prev_close_for_yesterday = round(hist.iloc[-3]["Close"], 4) if len(hist) >= 3 else yesterday_open
            yesterday_change = round((yesterday_close - prev_close_for_yesterday) / prev_close_for_yesterday * 100, 2) if prev_close_for_yesterday else 0.0
            
            yesterday_high_to_open_pct = round((yesterday_high - yesterday_open) / yesterday_open * 100, 2) if yesterday_open else 0.0
            yesterday_low_to_open_pct = round((yesterday_low - yesterday_open) / yesterday_open * 100, 2) if yesterday_open else 0.0
            today_high_to_open_pct = round((today_high - today_open) / today_open * 100, 2) if today_open else 0.0
            today_low_to_open_pct = round((today_low - today_open) / today_open * 100, 2) if today_open else 0.0
            
            rows.append({
                "Symbol": t,
                "Date": today_date,
                "Previous_Close": yesterday_close,
                "Open": today_open,
                "High": today_high,
                "Low": today_low,
                "Close": today_close,
                "High_to_Open_%": today_high_to_open_pct,
                "Low_to_Open_%": today_low_to_open_pct,
                "Close_Minus_Open": round(today_close - today_open, 4),
                "Previous_Volume": yesterday_vol,
                "Volume": today_vol,
                "Previous_Change %": yesterday_change,
                "Change %": today_change
            })
        except Exception as e:
            logger.error(f"Error fetching data for {t}: {e}")
            
    if not rows:
        logger.error("No data extracted to write.")
        return
        
    try:
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "Symbol", "Date", "Previous_Close", "Open", "High", "Low", "Close",
                "High_to_Open_%", "Low_to_Open_%", "Close_Minus_Open", 
                "Previous_Volume", "Volume", "Previous_Change %", "Change %"
            ])
            writer.writeheader()
            writer.writerows(rows)
        logger.info(f"Successfully wrote {len(rows)} rows to {out_path}")
    except Exception as e:
        logger.error(f"Failed to write CSV: {e}")

def main():
    parser = argparse.ArgumentParser(description="Fetch recent stock data (Open, Close, Volume, Change) for ASX tickers.")
    parser.add_argument("--tickers", type=str, required=True, help="Comma-separated list of tickers (e.g. CBA,CIA,XST)")
    parser.add_argument("--output", type=str, default="recent_stock_data.csv", help="Output filename in output/ directory")
    
    args = parser.parse_args()
    fetch_and_export(args.tickers, args.output)

if __name__ == "__main__":
    main()
