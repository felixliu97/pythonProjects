"""
ASX Database Manager

Manages the engine, session lifecycle, and provides robust transaction context managers.
Implements standardized SCD Type 2 logic for child tables.
"""

import os
import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Type

from sqlalchemy import create_engine, text, Engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from dotenv import load_dotenv

# Robust Environment Loading: Find .env relative to this file's directory (scripts/)
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

try:
    from db_models import Base
    from utils import logger
except ImportError:
    from scripts.db_models import Base
    from scripts.utils import logger

# DB Connection Config from Environment Variables (with explicit fallbacks)
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
ROOT_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/postgres"

class DBManager:
    """Manages database connections and session lifecycle."""
    
    def __init__(self):
        self._engine: Optional[Engine] = None
        self._SessionFactory: Optional[sessionmaker] = None
        self._scoped_session: Optional[scoped_session] = None

    def init_db(self, create_tables: bool = True):
        """Initialize the database connection and optionally create tables."""
        self.ensure_db_exists()
        # pool_pre_ping=True ensures stale connections are recycled
        self._engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
        self._SessionFactory = sessionmaker(bind=self._engine)
        self._scoped_session = scoped_session(self._SessionFactory)
        
        if create_tables:
            with self._engine.connect() as conn:
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS asx"))
                conn.commit()
            Base.metadata.create_all(self._engine)

    def ensure_db_exists(self):
        """Ensure the target database exists; if not, attempt minimal creation."""
        try:
            root_engine = create_engine(ROOT_URL, isolation_level="AUTOCOMMIT")
            with root_engine.connect() as conn:
                # Check for DB existence
                result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'"))
                if not result.fetchone():
                    logger.warning(f"Database {DB_NAME} not found. Creating...")
                    conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
            root_engine.dispose()
        except Exception as e:
            logger.debug(f"DB Existence check failed (likely no superuser): {e}")

    def get_session(self) -> Session:
        """Returns a thread-safe scoped session."""
        if not self._scoped_session:
            self.init_db()
        return self._scoped_session()

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            session.close()
    
    # Global DB Singleton
db = DBManager()
