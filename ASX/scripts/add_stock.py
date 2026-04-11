import argparse
import sys
import os

from scripts.db_manager import db
from scripts.db_models import Stock, CatalystMaster

def add_stock(ticker: str, company: str, sector: str, stock_type: str = "growth"):
    """Manually add a new stock to the tracking pipeline."""
    session = db.get_session()
    ticker = ticker.upper().strip()
    
    # 1. Add to Stocks table
    stock = session.query(Stock).filter_by(symbol=ticker).first()
    if not stock:
        stock = Stock(symbol=ticker, name=company, industry=sector, stock_type=stock_type)
        session.add(stock)
        session.flush()
        print(f"Added {ticker} to Core Stocks.")
    else:
        print(f"Stock {ticker} already exists.")
        
    # 2. Add to CatalystMaster
    master = session.query(CatalystMaster).filter_by(symbol=ticker).first()
    if not master:
        master = CatalystMaster(
            symbol=ticker,
            company=company,
            sector=sector,
            cr_risk="Unknown",
            probability="TBD",
            core_notes="Newly added stock. LLM update required."
        )
        session.add(master)
        session.flush()
        print(f"Initialized Catalyst Tracker for {ticker}.")
    else:
        print(f"Catalyst Tracker for {ticker} already exists.")

    session.commit()
    print("\nNext step: Run `python run.py llm-export --ticker {0}`".format(ticker))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add a new stock safely.")
    parser.add_argument("ticker", help="ASX code (ext: DXB)")
    parser.add_argument("company", help="Company Name in quotes")
    parser.add_argument("sector", help="Industry/Sector in quotes")
    parser.add_argument("--type", default="growth", choices=["growth", "foundation", "etf"], help="Stock type classification")
    
    args = parser.parse_args()
    add_stock(args.ticker, args.company, args.sector, args.type)
