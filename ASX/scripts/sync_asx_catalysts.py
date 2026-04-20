"""Sync ASX catalysts from YAML into DB without dropping schema.

This script performs an upsert on catalyst master rows and an SCD Type 2 sync
on catalyst_items (child lists) for each symbol.

Source of truth: config/asx_catalysts.yaml
"""

from __future__ import annotations

from datetime import datetime

import yaml

try:
    from db_manager import db
    from db_models import Stock, CatalystMaster, CatalystItem
    from db_schemas import validate_catalyst_records
    from utils import logger, get_sydney_time
except ImportError:
    from scripts.db_manager import db
    from scripts.db_models import Stock, CatalystMaster, CatalystItem
    from scripts.db_schemas import validate_catalyst_records
    from scripts.utils import logger, get_sydney_time


def sync_from_yaml(yaml_path: str = "config/asx_catalysts.yaml") -> None:
    db.init_db(create_tables=True)

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []

    validated_records = validate_catalyst_records(data)
    yaml_symbols = {record.Ticker for record in validated_records}

    now = get_sydney_time().replace(tzinfo=None)
    synced = 0
    deleted = 0

    with db.session_scope() as sess:
        existing_symbols = {
            symbol for (symbol,) in sess.query(CatalystMaster.symbol).all()
        }
        symbols_to_delete = existing_symbols - yaml_symbols

        if symbols_to_delete:
            deleted = sess.query(CatalystItem).filter(CatalystItem.symbol.in_(symbols_to_delete)).delete(synchronize_session=False)
            sess.query(CatalystMaster).filter(CatalystMaster.symbol.in_(symbols_to_delete)).delete(synchronize_session=False)

        for v_c in validated_records:
            sym = v_c.Ticker

            # Ensure Stock exists (soft requirement for dashboard joins)
            stock = sess.query(Stock).filter_by(symbol=sym).first()
            if not stock:
                sess.add(Stock(symbol=sym, name=v_c.Company, industry=v_c.Sector, stock_type="growth"))

            master = sess.query(CatalystMaster).filter_by(symbol=sym).first()
            if not master:
                master = CatalystMaster(symbol=sym)
                sess.add(master)

            master.stage = v_c.Stage or "未分类"
            master.company = v_c.Company
            master.sector = v_c.Sector
            master.cr_risk = v_c.CR_Risk
            master.cr_risk_reason = v_c.CR_Risk_Reason
            master.breakout_probability = v_c.Breakout_Probability
            master.breakout_probability_reason = v_c.Breakout_Probability_Reason
            master.core_notes = v_c.Core_Notes
            master.rating = v_c.Rating

            # Child SCD2 sync
            db.sync_list_data(sess, CatalystItem, "symbol", sym, v_c.Catalysts, item_type="catalyst", now=now)
            db.sync_list_data(sess, CatalystItem, "symbol", sym, v_c.Risks, item_type="risk", now=now)
            db.sync_list_data(sess, CatalystItem, "symbol", sym, v_c.Timeline, item_type="milestone", now=now)

            synced += 1

    logger.info(f"Synced {synced} catalyst masters from {yaml_path}; removed {len(symbols_to_delete)} masters and {deleted} child rows not present in YAML.")


if __name__ == "__main__":
    sync_from_yaml()
