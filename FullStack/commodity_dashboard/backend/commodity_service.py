import yfinance as yf
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict

# Local Cache Path
CACHE_FILE = os.path.join(os.path.dirname(__file__), "commodities_cache.json")
CACHE_THRESHOLD_MINUTES = 5

TICKERS = [
    {"ticker": "GC=F", "name": "Gold", "unit": "oz", "category": "Precious Metals", "icon": "Coins"},
    {"ticker": "SI=F", "name": "Silver", "unit": "oz", "category": "Precious Metals", "icon": "Disc"},
    {"ticker": "PL=F", "name": "Platinum", "unit": "oz", "category": "Precious Metals", "icon": "Sparkles"},
    {"ticker": "PA=F", "name": "Palladium", "unit": "oz", "category": "Precious Metals", "icon": "Zap"},
    {"ticker": "CL=F", "name": "Crude Oil WTI", "unit": "bbl", "category": "Energy", "icon": "Droplets"},
    {"ticker": "BZ=F", "name": "Brent Crude", "unit": "bbl", "category": "Energy", "icon": "Droplets"},
    {"ticker": "NG=F", "name": "Natural Gas", "unit": "MMBtu", "category": "Energy", "icon": "Wind"},
    {"ticker": "RB=F", "name": "Gasoline", "unit": "gal", "category": "Energy", "icon": "Droplet"},
    {"ticker": "HG=F", "name": "Copper", "unit": "lb", "category": "Industrial Metals", "icon": "Hammer"},
    {"ticker": "ALI=F", "name": "Aluminium", "unit": "mt", "category": "Industrial Metals", "icon": "Layers"},
    {"ticker": "ZN=F", "name": "Zinc", "unit": "mt", "category": "Industrial Metals", "icon": "Shield"},
    {"ticker": "TIO=F", "name": "Iron Ore", "unit": "mt", "category": "Industrial Metals", "icon": "Box"},
    {"ticker": "ZC=F", "name": "Corn", "unit": "bu", "category": "Agriculture", "icon": "Leaf"},
    {"ticker": "ZS=F", "name": "Soybeans", "unit": "bu", "category": "Agriculture", "icon": "Sprout"},
    {"ticker": "ZW=F", "name": "Wheat", "unit": "bu", "category": "Agriculture", "icon": "Wheat"},
    {"ticker": "KC=F", "name": "Coffee", "unit": "lb", "category": "Agriculture", "icon": "Coffee"},
    {"ticker": "SB=F", "name": "Sugar", "unit": "lb", "category": "Agriculture", "icon": "Candy"},
    {"ticker": "CT=F", "name": "Cotton", "unit": "lb", "category": "Agriculture", "icon": "Cloud"},
]

class CommodityService:
    @staticmethod
    def get_cached_data() -> Dict:
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    @staticmethod
    def save_to_cache(data: List[Dict]):
        cache_content = {
            "timestamp": datetime.now().isoformat(),
            "items": data
        }
        with open(CACHE_FILE, "w") as f:
            json.dump(cache_content, f, indent=2)

    @staticmethod
    async def fetch_real_time_commodities() -> List[Dict]:
        import asyncio
        loop = asyncio.get_event_loop()
        
        cache = CommodityService.get_cached_data()
        
        # Check Cache Threshold (5 minutes)
        if cache and "timestamp" in cache:
            try:
                last_fetch = datetime.fromisoformat(cache["timestamp"])
                if datetime.now() - last_fetch < timedelta(minutes=CACHE_THRESHOLD_MINUTES):
                    # print(f"Serving from cache (Last updated: {cache['timestamp']})")
                    return cache["items"]
            except Exception:
                pass

        print("Fetching fresh data from yfinance...")
        
        ticker_symbols = [t["ticker"] for t in TICKERS]
        try:
            # 使用 wait_for 增加超时保护以防 yfinance 挂起
            data = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: yf.download(ticker_symbols, period="1d", group_by='ticker', threads=True)),
                timeout=15  # 15秒超时
            )
            
            fresh_items = []
            for t_info in TICKERS:
                symbol = t_info["ticker"]
                try:
                    # 尝试从 yfinance 对象中提取价格
                    # 下载的数据结构可能是 MultiIndex DataFrame
                    ticker_data = data[symbol] if symbol in data.columns.levels[0] else None
                    if ticker_data is not None and not ticker_data.empty:
                        current_price = float(ticker_data['Close'].dropna().iloc[-1])
                        prev_close = float(ticker_data['Open'].dropna().iloc[-1])
                        change_abs = current_price - prev_close
                        change_pct = (change_abs / prev_close) * 100
                        
                        trend = "Neutral"
                        if change_pct > 0.5: trend = "Bullish"
                        elif change_pct < -0.5: trend = "Bearish"

                        fresh_items.append({
                            "ticker": symbol,
                            "name": t_info["name"],
                            "price": round(current_price, 2),
                            "unit": t_info["unit"],
                            "change_pct": round(change_pct, 2),
                            "change_abs": round(change_abs, 2),
                            "category": t_info["category"],
                            "icon": t_info["icon"],
                            "trend": trend,
                            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                except Exception as e:
                    print(f"Error processing {symbol}: {e}")
            
            if fresh_items:
                CommodityService.save_to_cache(fresh_items)
                return fresh_items
                
        except asyncio.TimeoutError:
            print("yfinance fetch timed out. Serving stale cache.")
        except Exception as e:
            print(f"Bulk fetch failed: {e}")
        
        # Final Fallback to Cache if everything failed
        if cache and "items" in cache:
            return cache["items"]
            
        # Last resort: empty list or error
        return []
