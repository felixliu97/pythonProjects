import yaml
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os

YAML_PATH = "config/asx_placements.yaml"

def fetch_liquidity(row):
    sym = row.get("ASX_Code", "")
    if not sym:
        return row, True, "No symbol"
        
    try:
        ticker = yf.Ticker(f"{sym}.AX")
        info = ticker.info
        
        # Sometime yfinance returns empty info for delisted/suspended stocks
        if not info or 'regularMarketPrice' not in info:
            # Let's try to get history as fallback to check if it's trading
            hist = ticker.history(period="10d")
            if hist.empty:
                return row, False, "No data/Delisted"
            # Estimate from history
            mcap = info.get("marketCap", 0) if info else 0
            avg_vol = hist["Volume"].mean()
            price = hist["Close"].iloc[-1]
            val = avg_vol * price
            
            if mcap > 0 and mcap < 10_000_000:
                return row, False, f"MCap < 10M (${mcap:,.0f})"
            if val < 20_000:
                return row, False, f"Avg Daily Val < 20k (${val:,.0f})"
            return row, True, "OK"
            
        mcap = info.get("marketCap", 0)
        avg_vol = info.get("averageVolume", info.get("regularMarketVolume", 0))
        price = info.get("regularMarketPrice", info.get("currentPrice", 0))
        
        if not price and 'previousClose' in info:
            price = info['previousClose']
            
        # fallback to history if info is incomplete
        if not avg_vol or not price:
            hist = ticker.history(period="10d")
            if hist.empty:
                return row, False, "No trading data"
            avg_vol = hist["Volume"].mean()
            price = hist["Close"].iloc[-1]
            
        daily_val = avg_vol * price
        
        if mcap > 0 and mcap < 10_000_000:
            return row, False, f"MCap < 10M (${mcap:,.0f})"
        
        if daily_val < 20_000:
            return row, False, f"Avg Daily Val < 20k (${daily_val:,.0f})"
            
        return row, True, "OK"
        
    except Exception as e:
        return row, True, f"Error, kept for safety ({str(e)})"

def main():
    print(f"Loading {YAML_PATH}...")
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    if not data:
        print("Empty YAML.")
        return
        
    print(f"Total rows: {len(data)}. Unique symbols: {len(set(r['ASX_Code'] for r in data if r.get('ASX_Code')))}")
        
    results = []
    removed = []
    
    # Process only unique symbols to save API calls
    unique_symbols = list(set(r.get("ASX_Code") for r in data if r.get("ASX_Code")))
    symbol_status = {}
    
    print("Fetching liquidity data...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_liquidity, {"ASX_Code": sym}): sym for sym in unique_symbols}
        done = 0
        for future in as_completed(futures):
            sym = futures[future]
            _, is_liquid, reason = future.result()
            symbol_status[sym] = (is_liquid, reason)
            done += 1
            if done % 10 == 0:
                print(f"Processed {done}/{len(unique_symbols)}...")
                
    for row in data:
        sym = row.get("ASX_Code")
        if not sym:
            results.append(row)
            continue
            
        is_liquid, reason = symbol_status.get(sym, (True, "Unchecked"))
        if is_liquid:
            results.append(row)
        else:
            removed.append((sym, reason))
            
    # Deduplicate removed list for printing
    unique_removed = list(set(removed))
    unique_removed.sort()
    
    print(f"\n--- Removed {len(unique_removed)} illiquid symbols ---")
    for sym, reason in unique_removed:
         print(f"{sym}: {reason}")
         
    # Write back
    print(f"\nWriting {len(results)} rows back to {YAML_PATH}...")
    with open(YAML_PATH, "w", encoding="utf-8") as f:
        yaml.dump(results, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
    print("Done. You should run `python run.py placements-html` to regenerate the dashboard.")

if __name__ == "__main__":
    main()
