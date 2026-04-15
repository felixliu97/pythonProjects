"""
ASX Catalyst JSON Generator (Best Practice Refactor)

Aggregates fundamental research from the database and exports a 
structured JSON file for the dashboard frontend.
"""

import sys
import json
import os
from typing import List, Dict, Any

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

def export_catalysts():
    """Aggregate DB records into the JSON format expected by asx_dashboard.html."""
    logger.info("Generating Catalyst JSON for dashboard...")
    
    output_path = get_root_dir() / "output" / "asx_catalysts.json"
    output_path.parent.mkdir(exist_ok=True)
    
    with db.session_scope() as sess:
        masters = sess.query(CatalystMaster).all()
        export_data = []
        
        for master in masters:
            try:
                # 1. Gather child items manually (Total Decoupling)
                active_items = sess.query(CatalystItem).filter_by(
                    symbol=master.symbol, 
                    is_active=True
                ).all()
                
                catalysts = [i.content for i in active_items if i.item_type == 'catalyst']
                risks = [i.content for i in active_items if i.item_type == 'risk']
                earnings = [i.content for i in active_items if i.item_type == 'earnings']
                timeline = [{"Time": i.label, "Event": i.content} for i in active_items if i.item_type == 'milestone']
                
                # 2. Map to Schema for final validation/serialization
                v = CatalystSchema(
                    Ticker=master.symbol,
                    Company=master.company,
                    Sector=master.sector or "Unknown",
                    Catalysts=catalysts,
                    Risks=risks,
                    Earnings_Window=earnings,
                    CR_Risk=master.cr_risk or "Unknown",
                    CR_Risk_Reason=master.cr_risk_reason or "",
                    Breakout_Probability=master.breakout_probability or "N/A",
                    Breakout_Probability_Reason=master.breakout_probability_reason or "",
                    Core_Notes=master.core_notes or "",
                    Rating=master.rating or "观望",
                    Timeline=timeline
                )
                
                # Use model_dump for clean dict with aliased names if any
                export_data.append(v.model_dump())
            except Exception as e:
                logger.error(f"Failed to export {master.symbol}: {e}")
                
        # Write JSON
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Catalysts Sync: Exported {len(export_data)} records to {output_path}")
        except Exception as e:
            logger.error(f"Failed to write JSON output: {e}")

if __name__ == "__main__":
    export_catalysts()
