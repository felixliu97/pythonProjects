"""
ASX LLM Integration Workflow (Refactored)

Provides high-fidelity data extraction for LLM fundamental research
and smart synchronization of updated research back to the database.
"""

import yaml
from datetime import datetime
from pathlib import Path

# Local Imports
try:
    from db_manager import db
    from db_models import CatalystMaster, CatalystItem
    from db_schemas import CatalystSchema
    from utils import logger, get_root_dir
except ImportError:
    from scripts.db_manager import db
    from scripts.db_models import CatalystMaster, CatalystItem
    from scripts.db_schemas import CatalystSchema
    from scripts.utils import logger, get_root_dir

def export_for_llm(tickers: str):
    """Export fundamental data for one or more stocks to a temporary YAML for LLM editing."""
    session = db.get_session()
    
    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    if "ALL" in ticker_list:
        masters = session.query(CatalystMaster).all()
    else:
        masters = session.query(CatalystMaster).filter(CatalystMaster.symbol.in_(ticker_list)).all()
    
    if not masters:
        logger.error(f"No matching stocks found in database for {tickers}.")
        return

    export_data = []
    for master in masters:
        items = master.items
        catalysts = [i.content for i in items if i.is_active and i.item_type == 'catalyst']
        risks = [i.content for i in items if i.is_active and i.item_type == 'risk']
        earnings = [i.content for i in items if i.is_active and i.item_type == 'earnings']
        timeline = [{"Time": i.label, "Event": i.content} for i in items if i.is_active and i.item_type == 'milestone']

        export_data.append({
            "Ticker": master.symbol,
            "Company": master.company,
            "Sector": master.sector,
            "Catalysts": catalysts,
            "Risks": risks,
            "Earnings_Window": earnings,
            "CR_Risk": master.cr_risk,
            "Probability": master.probability,
            "Core_Notes": master.core_notes,
            "Timeline": timeline
        })
    
    output_path = get_root_dir() / "config" / "temp_update.yaml"
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(export_data, f, allow_unicode=True, sort_keys=False)
    
    logger.info(f"Exported {len(export_data)} records to {output_path}. You can now use an LLM to update this file.")

def import_from_llm():
    """Import updated fundamental data and perform SCD Type 2 sync on details."""
    input_path = get_root_dir() / "config" / "temp_update.yaml"
    if not input_path.exists():
        logger.error(f"Import file not found: {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data:
        logger.error("No data found in YAML file.")
        return
        
    # Support both single object (legacy) and list of objects
    if isinstance(data, dict):
        data = [data]

    session = db.get_session()
    success_count = 0
    
    for item_data in data:
        try:
            valid_c = CatalystSchema(**item_data)
            master = session.query(CatalystMaster).filter_by(symbol=valid_c.Ticker).first()
            
            if not master:
                logger.warning(f"Could not find {valid_c.Ticker} in database to sync. Skipping.")
                continue

            with db.session_scope() as sess:
                # 1. Update Master Metadata
                master = sess.merge(master) # Ensure attached to this session
                master.company = valid_c.Company
                master.sector = valid_c.Sector
                master.cr_risk = valid_c.CR_Risk
                master.probability = valid_c.Probability
                master.core_notes = valid_c.Core_Notes
                
                # 2. Smart Sync Child Records via refined sync_list_data
                db.sync_list_data(sess, CatalystItem, "symbol", master.symbol, valid_c.Catalysts, item_type='catalyst')
                db.sync_list_data(sess, CatalystItem, "symbol", master.symbol, valid_c.Risks, item_type='risk')
                db.sync_list_data(sess, CatalystItem, "symbol", master.symbol, valid_c.Earnings_Window, item_type='earnings')
                db.sync_list_data(sess, CatalystItem, "symbol", master.symbol, valid_c.Timeline, item_type='milestone')
                
            success_count += 1
            
        except Exception as e:
            logger.error(f"Import validation failed for {item_data.get('Ticker', 'Unknown')}: {e}")

    logger.info(f"Successfully synced {success_count}/{len(data)} fundamental updates to database.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "export" and len(sys.argv) > 2:
            export_for_llm(sys.argv[2])
        elif sys.argv[1] == "import":
            import_from_llm()
