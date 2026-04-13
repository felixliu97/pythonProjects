import pytest
import os
import sys
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.db_models import Base
from scripts.db_manager import DBManager

@event.listens_for(Base.metadata, "before_create")
def sqlite_strip_schema(target, connection, **kw):
    """Strip schema names for SQLite during testing."""
    if connection.engine.dialect.name == "sqlite":
        for table in target.tables.values():
            table.schema = None

@pytest.fixture(scope="session")
def engine():
    """Create a temporary in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture(scope="function")
def db_session(engine):
    """Provides a transactional session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
