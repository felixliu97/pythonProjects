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
    from utils import logger, get_sydney_time
except ImportError:
    from scripts.db_models import Base
    from scripts.utils import logger, get_sydney_time

def get_db_url() -> str:
    """Returns the database URL based on the current environment."""
    if os.getenv("TESTING") == "true":
        return "sqlite:///:memory:"
    
    user = os.getenv("DB_USER", "postgres")
    pw = os.getenv("DB_PASS", "postgres")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "postgres")
    return f"postgresql://{user}:{pw}@{host}:{port}/{db_name}"

def get_root_url() -> str:
    """Returns the root database URL for existence checks."""
    if os.getenv("TESTING") == "true":
        return "sqlite:///:memory:"
    
    user = os.getenv("DB_USER", "postgres")
    pw = os.getenv("DB_PASS", "postgres")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    return f"postgresql://{user}:{pw}@{host}:{port}/postgres"

class DBManager:
    """Manages database connections and session lifecycle."""
    
    def __init__(self):
        self._engine: Optional[Engine] = None
        self._SessionFactory: Optional[sessionmaker] = None
        self._scoped_session: Optional[scoped_session] = None

    def init_db(self, create_tables: bool = True):
        """Initialize the database connection and optionally create tables."""
        self.ensure_db_exists()
        url = get_db_url()
        
        # SQLite doesn't support schemas, so we strip them from metadata
        if "sqlite" in url:
            for table in Base.metadata.tables.values():
                table.schema = None
            if os.getenv("TESTING") == "true":
                logger.info("🛠️  Testing mode active: Using in-memory SQLite database.")
        
        # pool_pre_ping=True ensures stale connections are recycled
        if "sqlite" in url:
            self._engine = create_engine(url)
        else:
            self._engine = create_engine(url, pool_pre_ping=True, pool_size=10, max_overflow=20)
            
        self._SessionFactory = sessionmaker(bind=self._engine)
        self._scoped_session = scoped_session(self._SessionFactory)
        
        if create_tables:
            if "sqlite" not in url:
                with self._engine.connect() as conn:
                    conn.execute(text("CREATE SCHEMA IF NOT EXISTS asx"))
                    conn.commit()
            Base.metadata.create_all(self._engine)

    def ensure_db_exists(self):
        """Ensure the target database exists; if not, attempt minimal creation."""
        url = get_root_url()
        if "sqlite" in url:
            return
            
        try:
            root_engine = create_engine(url, isolation_level="AUTOCOMMIT")
            with root_engine.connect() as conn:
                # Check for DB existence
                db_name = os.getenv("DB_NAME", "postgres")
                result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'"))
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

    def sync_list_data(
        self,
        sess: Session,
        model_cls: Type,
        key_field: str,
        key_val: Any,
        new_list: List[Any],
        *,
        item_type: str,
        now: Optional[datetime] = None,
    ) -> None:
        """SCD Type 2 sync for list-like child data.

        Assumptions:
        - Child table uses flat storage with: key_field (e.g. symbol), item_type, content, label.
        - Active rows are indicated by is_active=True; retire rows by setting is_active=False and valid_to.
        - For milestones, input items are dicts: {"Time": ..., "Event": ...}.
        """
        if new_list is None:
            new_list = []

        now = now or get_sydney_time().replace(tzinfo=None)

        q = sess.query(model_cls).filter(
            getattr(model_cls, key_field) == key_val,
            model_cls.item_type == item_type,
            model_cls.is_active.is_(True),
        )
        active_rows = q.all()

        def norm_child(v: Any) -> tuple[Optional[str], str]:
            if item_type == "milestone":
                if not isinstance(v, dict):
                    return (None, str(v).strip())
                label = (v.get("Time") or "").strip() or None
                content = (v.get("Event") or "").strip()
                return (label, content)

            return (None, str(v).strip())

        desired = []
        seen: set[tuple[Optional[str], str]] = set()
        for v in new_list:
            k = norm_child(v)
            if not k[1]:
                continue
            if k in seen:
                continue
            seen.add(k)
            desired.append(k)

        existing = {(r.label.strip() if r.label else None, (r.content or "").strip()): r for r in active_rows}
        desired_set = set(desired)

        # Retire missing
        for k, row in existing.items():
            if k not in desired_set:
                row.is_active = False
                row.valid_to = now

        # Insert new
        for label, content in desired:
            if (label, content) in existing:
                continue
            sess.add(
                model_cls(
                    **{key_field: key_val},
                    item_type=item_type,
                    content=content,
                    label=label,
                    valid_from=now,
                    is_active=True,
                )
            )

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
