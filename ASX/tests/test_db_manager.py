import pytest
from sqlalchemy import text
from scripts.db_manager import db
from scripts.db_models import Stock, MarketTrend

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# --- 1. Database Decoupling & Integrity ---

def test_flat_table_independence():
    """Verify that tables are standalone with no foreign key cascades."""
    symbol = "DECOUPLING_TEST"
    
    with db.session_scope() as sess:
        # Cleanup
        sess.query(Stock).filter_by(symbol=symbol).delete()
        sess.query(MarketTrend).filter_by(symbol=symbol).delete()
        sess.flush()
        
        from datetime import date
        # Inserts
        sess.add(Stock(symbol=symbol, name="Independent", stock_type="growth"))
        sess.add(MarketTrend(symbol=symbol, market_date=date(2026, 4, 13), score=99.9))
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


class _Base(DeclarativeBase):
    pass


class _Item(_Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), index=True)
    item_type = Column(String(50), index=True)
    content = Column(Text, nullable=False)
    label = Column(String(200))
    valid_from = Column(DateTime)
    valid_to = Column(DateTime)
    is_active = Column(Boolean, default=True, index=True)


@pytest.fixture()
def _mem_sess():
    engine = create_engine("sqlite:///:memory:")
    _Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    sess = Session()
    try:
        yield sess
    finally:
        sess.close()


def test_sync_list_data_inserts_and_retires(_mem_sess):
    now = datetime(2026, 4, 15, 12, 0, 0)

    _mem_sess.add(_Item(symbol="AAA", item_type="catalyst", content="A", valid_from=now, is_active=True))
    _mem_sess.add(_Item(symbol="AAA", item_type="catalyst", content="B", valid_from=now, is_active=True))
    _mem_sess.commit()

    db.sync_list_data(_mem_sess, _Item, "symbol", "AAA", ["A", "C"], item_type="catalyst", now=now)
    _mem_sess.commit()

    active = _mem_sess.query(_Item).filter_by(symbol="AAA", item_type="catalyst", is_active=True).all()
    retired = _mem_sess.query(_Item).filter_by(symbol="AAA", item_type="catalyst", is_active=False).all()

    assert sorted([r.content for r in active]) == ["A", "C"]
    assert [r.content for r in retired] == ["B"]
    assert retired[0].valid_to == now


def test_sync_list_data_milestone_label_mapping(_mem_sess):
    now = datetime(2026, 4, 15, 12, 0, 0)

    _mem_sess.add(
        _Item(
            symbol="AAA",
            item_type="milestone",
            label="2026-01-01",
            content="E1",
            valid_from=now,
            is_active=True,
        )
    )
    _mem_sess.commit()

    db.sync_list_data(
        _mem_sess,
        _Item,
        "symbol",
        "AAA",
        [{"Time": "2026-01-01", "Event": "E1"}, {"Time": "2026-02-01", "Event": "E2"}],
        item_type="milestone",
        now=now,
    )
    _mem_sess.commit()

    active = _mem_sess.query(_Item).filter_by(symbol="AAA", item_type="milestone", is_active=True).all()
    assert sorted([(r.label, r.content) for r in active]) == [("2026-01-01", "E1"), ("2026-02-01", "E2")]
