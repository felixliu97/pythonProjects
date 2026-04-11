import os
import sys
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

# Add the project root to sys.path to import scripts
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from scripts.db_models import Base
except ImportError:
    # If it fails, try adding the scripts directory directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))
    from db_models import Base

load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def check_consistency():
    try:
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)
        
        schema = "asx"
        tables = inspector.get_table_names(schema=schema)
        
        if not tables:
            print(f"Error: No tables found in schema '{schema}'.")
            return

        print(f"Tables found in schema '{schema}': {', '.join(tables)}\n")
        
        issues = []
        
        for model in Base.__subclasses__():
            table_name = model.__tablename__
            print(f"Checking table: {table_name}")
            
            if table_name not in tables:
                issues.append(f"Table '{table_name}' is missing in the database.")
                continue
            
            db_columns = {col['name']: col for col in inspector.get_columns(table_name, schema=schema)}
            model_columns = model.__table__.columns
            
            for col in model_columns:
                col_name = col.name
                if col_name not in db_columns:
                    issues.append(f"Column '{col_name}' is missing in database table '{table_name}'.")
                else:
                    # Basic type check (can be more detailed if needed)
                    db_col_type = str(db_columns[col_name]['type']).lower()
                    model_col_type = str(col.type).lower()
                    
                    # Some normalization for comparison
                    if "varchar" in model_col_type and "varchar" in db_col_type:
                        pass # Close enough for this check
                    elif "integer" in model_col_type and "integer" in db_col_type:
                        pass
                    elif "float" in model_col_type and "double precision" in db_col_type:
                        pass
                    elif "timestamp" in model_col_type and "timestamp" in db_col_type:
                        pass
                    elif "boolean" in model_col_type and "boolean" in db_col_type:
                        pass
                    elif "text" in model_col_type and "text" in db_col_type:
                        pass
                    elif "date" in model_col_type and "date" in db_col_type:
                        pass
                    elif "bigint" in model_col_type and "bigint" in db_col_type:
                        pass
                    else:
                        print(f"  Note: Column '{col_name}' type mismatch? Model: {model_col_type}, DB: {db_col_type}")

            # Check for extra columns in DB
            for col_name in db_columns:
                if col_name not in [c.name for c in model_columns]:
                    issues.append(f"Extra column '{col_name}' found in database table '{table_name}' (not in models).")

        if not issues:
            print("\nDatabase schema is consistent with models/DDL.")
        else:
            print("\nConsistency Issues Found:")
            for issue in issues:
                print(f"  - {issue}")

    except Exception as e:
        print(f"Error connecting to database: {e}")

if __name__ == "__main__":
    check_consistency()
