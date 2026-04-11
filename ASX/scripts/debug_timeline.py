import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))
from db_manager import db
from db_models import CatalystItem

def normalize_catalyst_date(time_str, current_year=2026):
    if not time_str: return "9999-12-31"
    t = time_str.upper().strip()
    
    if "Q1" in t: return f"{current_year}-03-31"
    if "H1" in t: return f"{current_year}-06-30"
    if "Q2" in t: return f"{current_year}-06-30"
    if "Q3" in t: return f"{current_year}-09-30"
    if "Q4" in t: return f"{current_year}-12-31"
    if "H2" in t: return f"{current_year}-12-31"
    
    if len(t) == 7 and t[4] == '-':
        return f"{t}-31"
    
    return t

def debug():
    session = db.get_session()
    items = session.query(CatalystItem).filter_by(item_type='milestone', is_active=True).all()
    
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    
    print(f"Debug Info:")
    print(f"Today: {today_str}")
    print(f"Total milestones in DB: {len(items)}")
    
    monthly_counts = {}
    for i in items:
        norm = normalize_catalyst_date(i.label)
        month = norm[:7]
        monthly_counts[month] = monthly_counts.get(month, 0) + 1
        
    print("\nMonthly Distribution (of Normalized Dates):")
    for m in sorted(monthly_counts.keys()):
        print(f"  {m}: {monthly_counts[m]} events")
    
    print("\nNext 3 Months Breakdown:")
    # April, May, June
    for i in items:
        norm = normalize_catalyst_date(i.label)
        if norm >= "2026-04-01" and norm <= "2026-06-30":
            print(f"  [{norm}] {i.master.symbol}: {i.label} -> {i.content[:40]}...")

if __name__ == "__main__":
    debug()

if __name__ == "__main__":
    debug()
