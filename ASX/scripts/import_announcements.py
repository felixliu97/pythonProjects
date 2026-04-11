import yaml
import os
import sys
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from scripts.db_manager import db
    from scripts.db_models import Stock, Announcement
    from scripts.db_schemas import AnnouncementSchema
    from scripts.utils import logger
except ImportError:
    from db_manager import db
    from db_models import Stock, Announcement
    from db_schemas import AnnouncementSchema
    from utils import logger

load_dotenv()

def import_announcements(file_path='config/asx_announcements.yaml'):
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return

    logger.info(f"Importing announcements from {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if not data:
        logger.warning("No data found in YAML file.")
        return

    session = db.get_session()
    count = 0
    new_stocks = 0
    
    # Get existing stock symbols to minimize DB hits
    existing_stocks = {s[0] for s in session.query(Stock.symbol).all()}
    
    for item in data:
        try:
            # Validate with schema
            v = AnnouncementSchema(**item)
            sym = v.ASX_Code
            
            # 1. Ensure stock exists (Foreign Key constraint)
            if sym not in existing_stocks:
                stock = Stock(symbol=sym, name=v.Company, stock_type='growth')
                session.add(stock)
                session.flush()
                existing_stocks.add(sym)
                new_stocks += 1
            
            # 2. Prepare Announcement data
            unique_key = f"{sym}_{v.Date}_{v.Headline[:100]}"
            
            # Using PostgreSQL-specific ON CONFLICT DO NOTHING (via SQLAlchemy insert)
            # Or just check existing. Since it's a small script, a simple check is fine.
            exists = session.query(Announcement).filter_by(unique_key=unique_key).first()
            if not exists:
                ann = Announcement(
                    symbol=sym,
                    company=v.Company,
                    headline=v.Headline,
                    event_date=v.Date,
                    summary=v.Summary,
                    pdf_link=v.PDF_Link,
                    rating=v.Rating,
                    unique_key=unique_key
                )
                session.add(ann)
                count += 1
                
                # Commit every 100 items to keep transaction size manageable
                if count % 100 == 0:
                    session.commit()
                    print(f"  Imported {count} items...")
                    
        except Exception as e:
            logger.debug(f"Skipped item due to error: {e}")
            continue
            
    session.commit()
    logger.info(f"Import complete: Added {count} announcements and registered {new_stocks} new stocks.")

if __name__ == "__main__":
    import_announcements()
