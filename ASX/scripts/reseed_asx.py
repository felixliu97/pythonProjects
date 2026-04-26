"""
ASX Database Reseed Utility (Best Practice Refactor)

Wipes the existing 'asx' schema and re-populates the database from
source YAML files in config/. This is the primary recovery tool.
Updated to use Pydantic V2 and SQLAlchemy 2.0.
"""

from datetime import datetime

import yaml
from sqlalchemy import text

try:
    from db_manager import db
    from db_models import CatalystItem, CatalystMaster, Placement, Stock
    from db_schemas import CatalystSchema, PlacementSchema, StockSchema
    from utils import logger
except ImportError:
    from scripts.db_manager import db
    from scripts.db_models import CatalystItem, CatalystMaster, Placement, Stock
    from scripts.db_schemas import CatalystSchema, PlacementSchema, StockSchema
    from scripts.utils import logger


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
        registered_symbols: set[str] = set()

        # 3. Stocks Ingestion
        logger.info("Seeding Stocks from analyzer config...")
        try:
            with open("config/asx_analyzer.yaml", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}

            categories = {"growth_stocks": "growth", "foundation_stocks": "foundation", "etfs": "etf"}

            for key, s_type in categories.items():
                for item in cfg.get(key, []):
                    try:
                        v_stock = StockSchema(stock_type=s_type, **item)
                        stock = Stock(
                            symbol=v_stock.symbol,
                            name=v_stock.name,
                            industry=v_stock.industry,
                            stock_type=v_stock.stock_type,
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
            with open("config/asx_catalysts.yaml", encoding="utf-8") as f:
                catalysts_data = yaml.safe_load(f) or []

            for item in catalysts_data:
                try:
                    v_c = CatalystSchema(**item)
                    ticker = v_c.Ticker

                    # Auto-create stock if missing from analyzer config
                    if ticker not in registered_symbols:
                        stock = Stock(symbol=ticker, name=v_c.Company, industry=v_c.Sector, stock_type="growth")
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
                        core_notes=v_c.Core_Notes,
                        rating=v_c.Rating,
                    )
                    sess.add(master)
                    sess.flush()

                    # Unified item creation
                    now = datetime.now()
                    for c in v_c.Catalysts:
                        sess.add(CatalystItem(symbol=ticker, item_type="catalyst", content=c, valid_from=now))
                    for r in v_c.Risks:
                        sess.add(CatalystItem(symbol=ticker, item_type="risk", content=r, valid_from=now))
                    for m in v_c.Timeline:
                        sess.add(
                            CatalystItem(
                                symbol=ticker,
                                item_type="milestone",
                                label=m.get("Time"),
                                content=m.get("Event"),
                                valid_from=now,
                            )
                        )
                except Exception as e:
                    logger.debug(f"Skipped invalid catalyst record {item.get('Ticker')}: {e}")
        except FileNotFoundError:
            logger.error("config/asx_catalysts.yaml not found.")

        def seed_scraped(file_path: str, schema_cls: type, model_cls: type, name: str):
            logger.info(f"Seeding {name}...")
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or []
                for item in data:
                    try:
                        v = schema_cls(**item)
                        sym = v.ASX_Code

                        if sym not in registered_symbols:
                            stock = Stock(symbol=sym, name=v.Company, stock_type="announcement")
                            sess.add(stock)
                            sess.flush()
                            registered_symbols.add(sym)

                        final_params = {
                            "symbol": sym,
                            "company": v.Company,
                            "headline": v.Headline,
                            "event_date": v.Date,
                            "cr_price": getattr(v, "CR_Price", None),
                            "current_price": getattr(v, "Current_Price", None),
                            "price_diff_percent": getattr(v, "Price_Diff_Percent", None),
                            "pdf_link": getattr(v, "PDF_Link", ""),
                        }

                        sess.add(model_cls(**final_params))
                    except Exception:
                        pass
            except FileNotFoundError:
                logger.warning(f"{file_path} not found.")

        seed_scraped("config/asx_placements.yaml", PlacementSchema, Placement, "Placements")

    logger.info("Reseed operation completed successfully.")


if __name__ == "__main__":
    reseed()
