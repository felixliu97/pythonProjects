"""
ASX Database Reseed Utility (Refactored)

Wipes the existing 'asx' schema and re-populates the database from 
source YAML files in config/. This is the primary recovery tool.
Updated to use 'symbol' as the primary/foreign key.
"""

import yaml
from datetime import datetime
from sqlalchemy import text
from typing import Dict, Set

# Local Imports
try:
    from db_manager import db
    from db_models import (
        Stock, CatalystMaster, CatalystItem, Announcement, Placement
    )
    from db_schemas import StockSchema, CatalystSchema, AnnouncementSchema, PlacementSchema
    from utils import logger, ticker_clean
except ImportError:
    from scripts.db_manager import db
    from scripts.db_models import (
        Stock, CatalystMaster, CatalystItem, Announcement, Placement
    )
    from scripts.db_schemas import StockSchema, CatalystSchema, AnnouncementSchema, PlacementSchema
    from scripts.utils import logger, ticker_clean

def reseed():
    """Wipe and re-seed the 'asx' schema from YAML files."""
    logger.warning("Initializing full database reseed from YAML source files...")
    
    # 0. Wipe schema
    engine = db.get_session().get_bind()
    with engine.connect() as conn:
        logger.info("Dropping existing 'asx' schema...")
        conn.execute(text("DROP SCHEMA IF EXISTS asx CASCADE"))
        conn.commit()
    
    # 1. Initialize Tables
    db.init_db(create_tables=True)
    session = db.get_session()
    now = datetime.now()

    registered_symbols: Set[str] = set()

    # 2. Stocks Ingestion
    logger.info("Seeding Stocks from analyzer config...")
    try:
        with open('config/asx_analyzer.yaml', 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
        
        categories = {
            'growth_stocks': 'growth', 
            'foundation_stocks': 'foundation', 
            'etfs': 'etf'
        }
        
        for key, s_type in categories.items():
            for item in cfg.get(key, []):
                try:
                    v_stock = StockSchema(stock_type=s_type, **item)
                    stock = Stock(
                        symbol=v_stock.symbol, 
                        name=v_stock.name, 
                        industry=v_stock.industry, 
                        stock_type=v_stock.stock_type
                    )
                    session.add(stock)
                    session.flush()
                    registered_symbols.add(v_stock.symbol)
                except Exception as e:
                    logger.debug(f"Invalid stock record filtered: {e}")
    except FileNotFoundError:
        logger.error("config/asx_analyzer.yaml not found.")

    # 3. Catalysts Ingestion
    logger.info("Seeding Catalyst items from master YAML...")
    try:
        with open('config/asx_catalysts.yaml', 'r', encoding='utf-8') as f:
            catalysts_data = yaml.safe_load(f)
        
        for item in catalysts_data:
            try:
                v_c = CatalystSchema(**item)
                ticker = v_c.Ticker
                
                # Auto-create stock if missing from analyzer config
                if ticker not in registered_symbols:
                    stock = Stock(symbol=ticker, name=v_c.Company, industry=v_c.Sector, stock_type='growth')
                    session.add(stock)
                    session.flush()
                    registered_symbols.add(ticker)
                    
                master = CatalystMaster(
                    symbol=ticker, 
                    company=v_c.Company,
                    sector=v_c.Sector, 
                    cr_risk=v_c.CR_Risk,
                    probability=v_c.Probability, 
                    core_notes=v_c.Core_Notes
                )
                session.add(master)
                session.flush()
                
                # Multi-type item creation
                for c in v_c.Catalysts: 
                    session.add(CatalystItem(symbol=ticker, item_type='catalyst', content=c, valid_from=now))
                for r in v_c.Risks: 
                    session.add(CatalystItem(symbol=ticker, item_type='risk', content=r, valid_from=now))
                for e in v_c.Earnings_Window: 
                    session.add(CatalystItem(symbol=ticker, item_type='earnings', content=e, valid_from=now))
                for m in v_c.Timeline: 
                    session.add(CatalystItem(
                        symbol=ticker, 
                        item_type='milestone', 
                        label=str(m.get('Time') or m.get('time_label', '')), 
                        content=m.get('Event') or m.get('event_desc', ''), 
                        valid_from=now
                    ))
            except Exception as e:
                logger.debug(f"Invalid catalyst record skipped: {e}")
    except FileNotFoundError:
        logger.error("config/asx_catalysts.yaml not found.")

    # 4. Announcements & Placements (Legacy Sync)
    def seed_scraped(file_path, schema_cls, model_cls, name):
        logger.info(f"Seeding {name}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            for item in data:
                try:
                    v = schema_cls(**item)
                    sym = v.ASX_Code
                    
                    # Auto-create stock if missing
                    if sym not in registered_symbols:
                        stock = Stock(symbol=sym, name=v.Company, stock_type='growth')
                        session.add(stock)
                        session.flush()
                        registered_symbols.add(sym)

                    params = v.model_dump()
                    # Custom mapping for SQLAlchemy
                    if name == "Announcements":
                        final_params = {
                            "symbol": sym,
                            "company": params.pop("Company"),
                            "headline": params.pop("Headline"),
                            "event_date": params.pop("Date"),
                            "summary": params.pop("Summary"),
                            "pdf_link": params.pop("PDF_Link"),
                            "rating": params.pop("Rating"),
                            "unique_key": f"{sym}_{params['Date']}_{params['Headline'][:100]}"
                        }
                    else:
                        final_params = {
                            "symbol": sym,
                            "company": params.pop("Company"),
                            "headline": params.pop("Headline"),
                            "event_date": params.pop("Date"),
                            "cr_price": params.pop("CR_Price"),
                            "current_price": params.pop("Current_Price"),
                            "price_diff_percent": params.pop("Price_Diff_Percent"),
                            "pdf_link": params.pop("PDF_Link")
                        }
                    
                    session.add(model_cls(**final_params))
                except Exception as e:
                    pass
        except FileNotFoundError:
            logger.warning(f"{file_path} not found.")

    seed_scraped('config/asx_announcements.yaml', AnnouncementSchema, Announcement, "Announcements")
    seed_scraped('config/asx_placements.yaml', PlacementSchema, Placement, "Placements")

    session.commit()
    logger.info("Reseed operation completed successfully.")

if __name__ == "__main__":
    reseed()
