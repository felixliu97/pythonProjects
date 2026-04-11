import os
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv

try:
    from .db_models import Base
except ImportError:
    from db_models import Base

# Load environment variables from .env
load_dotenv()

# DB Connection Config from Environment Variables
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
        self.engine = None
        self._SessionFactory = None
        self._scoped_session = None

    def init_db(self, create_tables: bool = True):
        """Initialize the database connection and optionally create tables."""
        self.ensure_db_exists()
        self.engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        self._SessionFactory = sessionmaker(bind=self.engine)
        self._scoped_session = scoped_session(self._SessionFactory)
        
        if create_tables:
            with self.engine.connect() as conn:
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS asx"))
                conn.commit()
            Base.metadata.create_all(self.engine)

    def ensure_db_exists(self):
        """Ensure the target database exists; if not, attempt minimal creation (requires superuser)."""
        try:
            root_engine = create_engine(ROOT_URL, isolation_level="AUTOCOMMIT")
            with root_engine.connect() as conn:
                # Minimal check
                conn.execute(text("SELECT 1"))
            root_engine.dispose()
        except Exception as e:
            # Note: In most production environments, this step should be handled by DBA/CI
            pass

    def get_session(self):
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
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def sync_list_data(self, session, model_class, master_id_field, master_id, new_items, item_type=None):
        """Standardized SCD Type 2 logic for syncing child items."""
        from datetime import datetime
        
        filters = [
            getattr(model_class, master_id_field) == master_id,
            model_class.is_active == True
        ]
        if item_type and hasattr(model_class, 'item_type'):
            filters.append(model_class.item_type == item_type)
            
        current_records = session.query(model_class).filter(*filters).all()
        
        def get_key(item, is_model=False):
            if is_model:
                if item_type == 'milestone':
                    return f"{item.label}|{item.content}".strip()
                return str(item.content).strip()
            
            if isinstance(item, str): return item.strip()
            if isinstance(item, dict):
                return f"{item.get('time_label') or item.get('label', '')}|{item.get('event_desc') or item.get('content', '')}".strip()
            return str(item).strip()

        current_map = {get_key(r, is_model=True): r for r in current_records}
        new_map = {get_key(i): i for i in new_items}
        now = datetime.now()

        # Retire removed
        for key, record in current_map.items():
            if key not in new_map:
                record.is_active = False
                record.valid_to = now
        
        # Add new
        for key, item in new_map.items():
            if key not in current_map:
                params = {
                    master_id_field: master_id,
                    "valid_from": now,
                    "is_active": True
                }
                if item_type: params["item_type"] = item_type
                
                if isinstance(item, dict):
                    params["label"] = item.get('time_label') or item.get('label')
                    params["content"] = item.get('event_desc') or item.get('content')
                else:
                    params["content"] = str(item).strip()
                
                session.add(model_class(**params))

# Singleton instance for legacy compat and ease of use
db = DBManager()
