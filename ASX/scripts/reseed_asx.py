"""
ASX Database Reseed Utility (Best Practice Refactor)

Wipes the existing 'asx' schema and re-populates the database from 
source YAML files in config/. This is the primary recovery tool.
Updated to use Pydantic V2 and SQLAlchemy 2.0.
"""

import yaml
from datetime import datetime
from sqlalchemy import text
from typing import Dict, Set, List, Any, Type

try:
    from db_manager import db
    from db_models import (
        Stock, CatalystMaster, CatalystItem, Announcement, Placement, Base
    )
    from db_schemas import StockSchema, CatalystSchema, AnnouncementSchema, PlacementSchema
    from utils import logger, ticker_clean
except ImportError:
    from scripts.db_manager import db
    from scripts.db_models import (
        Stock, CatalystMaster, CatalystItem, Announcement, Placement, Base
    )
    from scripts.db_schemas import StockSchema, CatalystSchema, AnnouncementSchema, PlacementSchema
    from scripts.utils import logger, ticker_clean

def reseed():
    """Wipe and re-seed the 'asx' schema from YAML files."""
    logger.warning("Initializing full database reseed from YAML source files...")
    
    # 0. Initialize System
    db.init_db(create_tables=False)
    engine = db.get_session().get_bind()
    
    # 1. Wipe schema
    with engine.connect() as conn:
        logger.info("Dropping existing 'asx' schema...")
        conn.execute(text("DROP SCHEMA IF EXISTS asx CASCADE"))
        conn.commit()
    
    # 2. Recreate Tables
    db.init_db(create_tables=True)
    
    with db.session_scope() as sess:
        registered_symbols: Set[str] = set()

        # 3. Stocks Ingestion
        logger.info("Seeding Stocks from analyzer config...")
        try:
            with open('config/asx_analyzer.yaml', 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f) or {}
            
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
                        sess.add(stock)
                        sess.flush()
                        registered_symbols.add(v_stock.symbol)
                    except Exception as e:
                        logger.debug(f"Filtered invalid stock record: {e}")
        except FileNotFoundError:
            logger.error("config/asx_analyzer.yaml not found.")

        # 4. Catalysts Ingestion
        logger.info("Seeding Catalyst items from master YAML...")
        try:
            with open('config/asx_catalysts.yaml', 'r', encoding='utf-8') as f:
                catalysts_data = yaml.safe_load(f) or []
            
            for item in catalysts_data:
                try:
                    v_c = CatalystSchema(**item)
                    ticker = v_c.Ticker
                    
                    # Auto-create stock if missing from analyzer config
                    if ticker not in registered_symbols:
                        stock = Stock(symbol=ticker, name=v_c.Company, industry=v_c.Sector, stock_type='growth')
                        sess.add(stock)
                        sess.flush()
                        registered_symbols.add(ticker)
                        
                    master = CatalystMaster(
                        symbol=ticker, 
                        company=v_c.Company,
                        sector=v_c.Sector, 
                        cr_risk=v_c.CR_Risk,
                        cr_risk_reason=v_c.CR_Risk_Reason,
                        breakout_probability=v_c.Breakout_Probability, 
                        breakout_probability_reason=v_c.Breakout_Probability_Reason,
                        core_notes=v_c.Core_Notes
                    )
                    sess.add(master)
                    sess.flush()
                    
                    # Unified item creation
                    now = datetime.now()
                    for c in v_c.Catalysts: 
                        sess.add(CatalystItem(symbol=ticker, item_type='catalyst', content=c, valid_from=now))
                    for r in v_c.Risks: 
                        sess.add(CatalystItem(symbol=ticker, item_type='risk', content=r, valid_from=now))
                    for e in v_c.Earnings_Window: 
                        sess.add(CatalystItem(symbol=ticker, item_type='earnings', content=e, valid_from=now))
                    for m in v_c.Timeline: 
                        sess.add(CatalystItem(
                            symbol=ticker, 
                            item_type='milestone', 
                            label=m.get('Time'), 
                            content=m.get('Event'), 
                            valid_from=now
                        ))
                except Exception as e:
                    logger.debug(f"Skipped invalid catalyst record {item.get('Ticker')}: {e}")
        except FileNotFoundError:
            logger.error("config/asx_catalysts.yaml not found.")

        # 5. Announcements & Placements (Legacy Sync)
        def seed_scraped(file_path: str, schema_cls: Type, model_cls: Type, name: str):
            logger.info(f"Seeding {name}...")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or []
                for item in data:
                    try:
                        v = schema_cls(**item)
                        sym = v.ASX_Code if hasattr(v, 'ASX_Code') else v.symbol
                        
                        if sym not in registered_symbols:
                            stock = Stock(symbol=sym, name=v.Company, stock_type='discovery')
                            sess.add(stock)
                            sess.flush()
                            registered_symbols.add(sym)

                        params = v.model_dump()
                        if name == "Announcements":
                            final_params = {
                                "symbol": sym,
                                "company": v.Company,
                                "headline": v.Headline,
                                "event_date": v.Date,
                                "summary": getattr(v, "Summary", ""),
                                "pdf_link": getattr(v, "PDF_Link", ""),
                                "rating": getattr(v, "Rating", 2),
                                "unique_key": f"{sym}_{v.Date}_{v.Headline[:100]}"
                            }
                        else:
                            final_params = {
                                "symbol": sym,
                                "company": v.Company,
                                "headline": v.Headline,
                                "event_date": v.Date,
                                "cr_price": getattr(v, "CR_Price", None),
                                "current_price": getattr(v, "Current_Price", None),
                                "price_diff_percent": getattr(v, "Price_Diff_Percent", None),
                                "pdf_link": getattr(v, "PDF_Link", "")
                            }
                        
                        sess.add(model_cls(**final_params))
                    except Exception:
                        pass
            except FileNotFoundError:
                logger.warning(f"{file_path} not found.")

        seed_scraped('config/asx_announcements.yaml', AnnouncementSchema, Announcement, "Announcements")
        seed_scraped('config/asx_placements.yaml', PlacementSchema, Placement, "Placements")

    logger.info("Reseed operation completed successfully.")

if __name__ == "__main__":
    reseed()
