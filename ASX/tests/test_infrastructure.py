import pytest
import os
from datetime import datetime
from sqlalchemy import text
from scripts.db_manager import db
from scripts.db_models import Stock, MarketTrend, CatalystMaster
from scripts.utils import ticker_clean, normalize_date, generate_sparkline

# --- 1. Utility Tests ---

def test_ticker_clean():
    assert ticker_clean("BHP.AX") == "BHP"
    assert ticker_clean("  RIO  ") == "RIO"
    assert ticker_clean(None) == ""

def test_normalize_date():
    assert normalize_date("2026-04-13T10:00:00+1000") == "2026-04-13"
    expected = datetime.now().strftime("%Y-%m-%d")
    assert normalize_date("") == expected

def test_generate_sparkline():
    svg_data = generate_sparkline("1.0,1.1,1.2")
    assert svg_data.startswith("data:image/svg+xml;base64,")

# --- 2. Database Decoupling & Integrity ---

def test_flat_table_independence():
    """Verify that tables are standalone with no foreign key cascades."""
    symbol = "DECOUPLING_TEST"
    
    with db.session_scope() as sess:
        # Cleanup
        sess.query(Stock).filter_by(symbol=symbol).delete()
        sess.query(MarketTrend).filter_by(symbol=symbol).delete()
        sess.flush()
        
        # Inserts
        sess.add(Stock(symbol=symbol, name="Independent", stock_type="growth"))
        sess.add(MarketTrend(symbol=symbol, market_date="2026-04-13", score=99.9))
        sess.commit()
        
    with db.session_scope() as sess:
        stock = sess.query(Stock).filter_by(symbol=symbol).first()
        # Verify no relationships
        assert not hasattr(stock, "market_trends")
        # Delete stock
        sess.delete(stock)
        sess.commit()
    
    with db.session_scope() as sess:
        # Verify MarketTrend SURVIVES (no cascade)
        trend = sess.query(MarketTrend).filter_by(symbol=symbol).first()
        assert trend is not None
        assert trend.score == 99.9
