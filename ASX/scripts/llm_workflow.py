"""
ASX LLM Integration Workflow (Best Practice Refactor)

Provides high-fidelity data extraction for LLM fundamental research
and smart synchronization of updated research back to the database.
"""

import yaml
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

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

class LLMWorkflow:
    """Manages fundamental research export/import for LLM-assisted updates."""
    
    def __init__(self):
        self.temp_file = get_root_dir() / "config" / "temp_update.yaml"

    def export_for_llm(self, tickers: str):
        """Export fundamental data for stocks to a temporary YAML."""
        logger.info(f"Exporting data for: {tickers}...")
        
        with db.session_scope() as sess:
            ticker_list = [t.strip().upper() for t in tickers.split(",")]
            if "ALL" in ticker_list:
                masters = sess.query(CatalystMaster).all()
            else:
                masters = sess.query(CatalystMaster).filter(CatalystMaster.symbol.in_(ticker_list)).all()
            
            if not masters:
                logger.error(f"No matching stocks found for {tickers}.")
                return

            export_data = []
            for master in masters:
                items = master.items
                active_items = [i for i in items if i.is_active]
                
                export_data.append({
                    "Ticker": master.symbol,
                    "Company": master.company,
                    "Sector": master.sector,
                    "Catalysts": [i.content for i in active_items if i.item_type == 'catalyst'],
                    "Risks": [i.content for i in active_items if i.item_type == 'risk'],
                    "Earnings_Window": [i.content for i in active_items if i.item_type == 'earnings'],
                    "CR_Risk": master.cr_risk,
                    "CR_Risk_Reason": master.cr_risk_reason,
                    "Breakout_Probability": master.breakout_probability,
                    "Breakout_Probability_Reason": master.breakout_probability_reason,
                    "Core_Notes": master.core_notes,
                    "Timeline": [{"Time": i.label, "Event": i.content} for i in active_items if i.item_type == 'milestone']
                })
        
        with open(self.temp_file, "w", encoding="utf-8") as f:
            yaml.dump(export_data, f, allow_unicode=True, sort_keys=False)
        
        logger.info(f"Exported {len(export_data)} records to {self.temp_file}")

    def import_from_llm(self):
        """Import updated fundamental data and Perform SCD Type 2 sync."""
        if not self.temp_file.exists():
            logger.error(f"Import file not found: {self.temp_file}")
            return

        try:
            with open(self.temp_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or []
            
            if isinstance(data, dict): data = [data]
            if not data: return

            with db.session_scope() as sess:
                success_count = 0
                for item_data in data:
                    try:
                        valid_c = CatalystSchema(**item_data)
                        master = sess.query(CatalystMaster).filter_by(symbol=valid_c.Ticker).first()
                        
                        if not master:
                            logger.warning(f"Ticker {valid_c.Ticker} not in DB. Skipping.")
                            continue

                        # 1. Update Master Attributes
                        master.company = valid_c.Company
                        master.sector = valid_c.Sector
                        master.core_notes = valid_c.Core_Notes
                        master.cr_risk = valid_c.CR_Risk
                        master.cr_risk_reason = valid_c.CR_Risk_Reason
                        master.breakout_probability = valid_c.Breakout_Probability
                        master.breakout_probability_reason = valid_c.Breakout_Probability_Reason
                        
                        # 2. Sync Child Lists (SCD Type 2)
                        db.sync_list_data(sess, CatalystItem, "symbol", master.symbol, valid_c.Catalysts, item_type='catalyst')
                        db.sync_list_data(sess, CatalystItem, "symbol", master.symbol, valid_c.Risks, item_type='risk')
                        db.sync_list_data(sess, CatalystItem, "symbol", master.symbol, valid_c.Earnings_Window, item_type='earnings')
                        db.sync_list_data(sess, CatalystItem, "symbol", master.symbol, valid_c.Timeline, item_type='milestone')
                        
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Import failed for {item_data.get('Ticker')}: {e}")
                
                logger.info(f"Successfully synced {success_count}/{len(data)} research updates.")
        except Exception as e:
            logger.error(f"Import process failed: {e}")

if __name__ == "__main__":
    workflow = LLMWorkflow()
    if len(sys.argv) > 1:
        if sys.argv[1] == "export" and len(sys.argv) > 2:
            workflow.export_for_llm(sys.argv[2])
        elif sys.argv[1] == "import":
            workflow.import_from_llm()
