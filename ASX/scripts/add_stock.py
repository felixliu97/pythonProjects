"""
ASX Add Stock Utility

Manually add a new stock to the database and initialize its fundamental research master.
"""

import sys
import argparse
from typing import Optional

try:
    from db_manager import db
    from db_models import Stock, CatalystMaster
    from db_schemas import StockSchema
    from utils import logger, ticker_clean
except ImportError:
    from scripts.db_manager import db
    from scripts.db_models import Stock, CatalystMaster
    from scripts.db_schemas import StockSchema
    from scripts.utils import logger, ticker_clean

def add_stock(symbol: str, name: str, industry: str, stock_type: str = "growth"):
    """Initialize a new stock record and its catalyst master."""
    clean_sym = ticker_clean(symbol)
    
    try:
        # 1. Validate with Schema
        v = StockSchema(
            symbol=clean_sym,
            name=name,
            industry=industry,
            stock_type=stock_type
        )
        
        with db.session_scope() as sess:
            # 2. Check existence
            existing = sess.query(Stock).filter_by(symbol=v.symbol).first()
            if existing:
                logger.warning(f"Stock {v.symbol} already exists. Updating metadata...")
                existing.name = v.name
                existing.industry = v.industry
                existing.stock_type = v.stock_type
            else:
                # 3. Create Stock
                stock = Stock(
                    symbol=v.symbol,
                    name=v.name,
                    industry=v.industry,
                    stock_type=v.stock_type
                )
                sess.add(stock)
                
            # 4. Initialize Catalyst Master if missing
            master = sess.query(CatalystMaster).filter_by(symbol=v.symbol).first()
            if not master:
                new_master = CatalystMaster(
                    symbol=v.symbol,
                    company=v.name,
                    sector=v.industry,
                    cr_risk="Unknown",
                    probability="N/A",
                    core_notes="Manual addition."
                )
                sess.add(new_master)
                
        logger.info(f"Successfully added/updated Stock: {v.symbol} ({v.name})")
    except Exception as e:
        logger.error(f"Failed to add stock {symbol}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add ASX Stock to Database")
    parser.add_argument("symbol", help="Ticker (e.g., BHP)")
    parser.add_argument("name", help="Company Name")
    parser.add_argument("industry", help="Industry/Sector")
    parser.add_argument("--type", default="growth", choices=["growth", "foundation", "etf"], help="Stock Type")
    
    args = parser.parse_args()
    add_stock(args.symbol, args.name, args.industry, args.type)
