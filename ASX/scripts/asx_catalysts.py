"""
ASX Catalyst Data Synchronization (Refactored)

Extracts consolidated fundamental data from the database and exports 
a structured JSON snapshot for the dashboard.
"""

import json
from datetime import datetime

# Local Imports
try:
    from db_manager import db
    from db_models import CatalystMaster
    from utils import logger, load_config
except ImportError:
    from scripts.db_manager import db
    from scripts.db_models import CatalystMaster
    from scripts.utils import logger, load_config

def process_catalysts():
    """Fetch sorted catalyst data from DB and export to JSON snapshot."""
    _CFG = load_config()
    JSON_OUT = _CFG["CAT_JSON_OUT"]
    
    session = db.get_session()
    results = session.query(CatalystMaster).all()
    
    stocks_data = []
    for m in results:
        # Use child relationship with item_type filtering
        items = m.items
        stock_item = {
            "Ticker": m.symbol,
            "Company": m.company,
            "Sector": m.sector,
            "Catalysts": [i.content for i in items if i.is_active and i.item_type == 'catalyst'],
            "Risks": [i.content for i in items if i.is_active and i.item_type == 'risk'],
            "Earnings_Window": [i.content for i in items if i.is_active and i.item_type == 'earnings'],
            "CR_Risk": m.cr_risk,
            "Probability": m.probability,
            "Core_Notes": m.core_notes,
            "Timeline": [{"Time": i.label, "Event": i.content} for i in items if i.is_active and i.item_type == 'milestone']
        }
        stocks_data.append(stock_item)

    # Export processed data for Dashboard usage
    with open(JSON_OUT, 'w', encoding='utf-8') as f:
        json.dump({
            'catalysts': stocks_data, 
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Catalysts Sync: Exported {len(stocks_data)} records to {JSON_OUT}")

if __name__ == "__main__":
    process_catalysts()
