import pytest
from sqlalchemy import text
from scripts.db_manager import db
from scripts.db_models import Stock, MarketTrend

# --- 1. Database Decoupling & Integrity ---

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
