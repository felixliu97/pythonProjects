"""
ASX Research Pipeline - Main Orchestrator (Refactored)

Central entry point for the ASX research database pipeline.
Handles scraping, analysis, database management, and UI generation.
"""

import sys
import os
import argparse
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Local Imports
try:
    from scripts.db_manager import db
    from scripts.db_models import Stock, CatalystMaster, Announcement, Placement, CatalystItem, MarketTrend
    from scripts.utils import logger, load_config, get_root_dir, generate_sparkline, get_sydney_time
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), "scripts"))
    from db_manager import db
    from db_models import Stock, CatalystMaster, Announcement, Placement, CatalystItem, MarketTrend
    from utils import logger, load_config, get_root_dir, generate_sparkline, get_sydney_time

def trim_zeros(value):
    """Jinja2 filter to trim trailing zeros from floats, max 4 decimals."""
    if value is None or value == "": return ""
    try:
        f_val = float(value)
        # Force round to 4 decimals first
        s = f"{f_val:.4f}"
        if '.' in s:
            s = s.rstrip('0').rstrip('.')
        return s
    except (ValueError, TypeError):
        return str(value)

def run_script(script_path: str, args: list = None) -> bool:
    """Execute a Python script relative to the root directory."""
    root_dir = get_root_dir()
    full_path = root_dir / script_path
    if not full_path.exists():
        logger.error(f"Script not found: {full_path}")
        return False
        
    cmd = [sys.executable, str(full_path)] + (args or [])
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, cwd=str(root_dir), check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Execution failed for {script_path}: {e}")
        return False

def load_db_data() -> dict:
    """Fetch consolidated data from the database using explicit queries (Decoupled Edition)."""
    with db.session_scope() as session:
        # 1. Catalyst Data
        masters = session.query(CatalystMaster).all()
        catalysts_list = []
        for m in masters:
            # Latest Market Trend
            trend = session.query(MarketTrend).filter_by(symbol=m.symbol, is_active=True).order_by(MarketTrend.id.desc()).first()
            
            # Explicit query instead of m.items
            items = session.query(CatalystItem).filter_by(symbol=m.symbol, is_active=True).all()
            
            catalysts_list.append({
                "Ticker": m.symbol,
                "Company": m.company,
                "Sector": m.sector,
                "Rating": m.rating or "观望",
                "Catalysts": [i.content for i in items if i.item_type == 'catalyst'],
                "Risks": [i.content for i in items if i.item_type == 'risk'],
                "Earnings_Window": [i.content for i in items if i.item_type == 'earnings'],
                "CR_Risk": m.cr_risk or "Unknown",
                "CR_Risk_Reason": m.cr_risk_reason or "",
                "Breakout_Probability": m.breakout_probability or "N/A",
                "Breakout_Probability_Reason": m.breakout_probability_reason or "",
                "Core_Notes": m.core_notes,
                "Timeline": sorted(
                    [
                        {"Time": label, "Event": "; ".join(contents)}
                        for label, contents in {
                            m.label: list(dict.fromkeys([m2.content for m2 in items if m2.item_type == 'milestone' and m2.label == m.label]))
                            for m in items if m.item_type == 'milestone'
                        }.items()
                    ],
                    key=lambda x: x['Time']
                )
            })
        
        def breakout_key(s):
            rating = s.get("Rating", "观望")
            r_scores = {"强力买入": -10, "买入": -5, "观望": 0, "卖出": 5, "强力卖出": 10}
            r_val = r_scores.get(rating, 0)
            
            p = (s.get("Breakout_Probability") or "").strip()
            p_scores = {"极高": -6, "高": -5, "中高": -4, "中": -3, "中低": -2, "低": -1}
            p_val = next((v for k, v in p_scores.items() if p.startswith(k)), 0)
            
            cr = (s.get("CR_Risk") or "").strip()
            cr_scores = {"极低": 1, "低": 2, "中低": 3, "中": 4, "中高": 5, "高": 6}
            cr_val = next((v for k, v in cr_scores.items() if cr.startswith(k)), 10)
            
            return (r_val, p_val, cr_val, (s.get("Ticker") or ""))
        
        catalysts_list.sort(key=breakout_key)

        # 2. Announcements (Last 14 days)
        cutoff = (get_sydney_time() - timedelta(days=14)).date()
        ann_res = session.query(Announcement).filter(
            Announcement.event_date >= cutoff
        ).order_by(
            Announcement.event_date.desc(), 
            Announcement.rating.desc()
        ).all()
        ann_list = [{
            "ASX_Code": a.symbol,
            "Company": a.company,
            "Headline": a.headline,
            "Date": a.event_date.strftime("%Y-%m-%d") if a.event_date else "",
            "Summary": a.summary,
            "PDF_Link": a.pdf_link,
            "Rating": a.rating
        } for a in ann_res]

        # 3. Placements
        plac_res = session.query(Placement).order_by(Placement.event_date.desc()).limit(150).all()
        plac_list = [{
            "ASX_Code": p.symbol,
            "Company": p.company,
            "Headline": p.headline,
            "Date": p.event_date.strftime("%Y-%m-%d") if p.event_date else "",
            "CR_Price": p.cr_price,
            "Current_Price": p.current_price,
            "Price_Diff_%": p.price_diff_percent or 0.0,
            "PDF_Link": p.pdf_link
        } for p in plac_res]

        # 4. Market Trends (Categorized for Template)
        trends = session.query(MarketTrend).filter_by(is_active=True).all()
        
        # Build a stock lookup cache to avoid N+1 queries during categorization
        stocks = session.query(Stock).all()
        stock_map = {s.symbol: s for s in stocks}

        analyzer_data = {
            "growth_stocks": [],
            "foundation_stocks": [],
            "etfs": [],
            "global_timeline": []
        }
        
        for t in trends:
            stock = stock_map.get(t.symbol)
            if not stock: continue
            
            s_obj = {
                "symbol": t.symbol,
                "name": stock.name,
                "industry": stock.industry,
                "current_price": t.current_price or 0.0,
                "marketCap": t.market_cap or 0,
                "pe": t.pe,
                "yield": t.yield_val or 0.0,
                "score": t.score or 0.0,
                "price_change_1d": t.price_change_1d or 0.0,
                "price_diff_1d": t.price_diff_1d or 0.0,
                "price_change_5d": t.price_change_5d or 0.0,
                "price_diff_5d": t.price_diff_5d or 0.0,
                "momentum": t.momentum or 0.0,
                "volatility": t.volatility or 0.0,
                "volume_change": t.volume_change or 0.0,
                "rsi": t.rsi or 50.0,
                "sparkline": generate_sparkline(t.price_history)
            }
            if stock.stock_type == 'growth': analyzer_data["growth_stocks"].append(s_obj)
            elif stock.stock_type == 'foundation': analyzer_data["foundation_stocks"].append(s_obj)
            elif stock.stock_type == 'etf': analyzer_data["etfs"].append(s_obj)

        return {
            "analyzer": analyzer_data,
            "catalysts": {"catalysts": catalysts_list},
            "announcements": {"announcements": ann_list},
            "placements": {"placements": plac_list},
            "timestamp": get_sydney_time().strftime("%Y-%m-%d %H:%M:%S")
        }

def build_dashboard():
    """Render the dashboard using Jinja2 templates."""
    logger.info("Generating Dashboard HTML...")
    root_dir = get_root_dir()
    template_dir = root_dir / "templates"
    output_path = root_dir / "output" / "asx_dashboard.html"
    
    # Ensure output directory exists
    output_path.parent.mkdir(exist_ok=True)
    
    data = load_db_data()
    
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    env.filters["trim_zeros"] = trim_zeros
    
    template = env.get_template("asx_dashboard.html")
    
    html_content = template.render(**data)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    logger.info(f"Dashboard successfully updated: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="ASX Research Hub Control Center")
    parser.add_argument("command", choices=["all", "scrape", "analyze", "dashboard", "reseed", "llm-export", "llm-import"], help="Pipeline command to run")
    parser.add_argument("--ticker", help="Specific ticker for LLM operations")
    parser.add_argument("--force", action="store_true", help="Force a full refresh (ignore incremental sync)")
    args = parser.parse_args()

    # Shared flags for scrapers
    scrape_args = ["--full-refresh"] if args.force else []

    if args.command == "reseed":
        run_script("scripts/reseed_asx.py")
    elif args.command == "scrape":
        run_script("scripts/asx_announcements.py", scrape_args)
        run_script("scripts/asx_placements.py", scrape_args)
    elif args.command == "analyze":
        run_script("scripts/asx_analyzer.py")
        run_script("scripts/asx_catalysts.py")
    elif args.command == "dashboard":
        build_dashboard()
    elif args.command == "all":
        run_script("scripts/asx_announcements.py", scrape_args)
        run_script("scripts/asx_placements.py", scrape_args)
        run_script("scripts/asx_analyzer.py")
        run_script("scripts/asx_catalysts.py")
        build_dashboard()
    elif args.command == "llm-export":
        if not args.ticker:
            logger.error("LLM Export requires --ticker <SYMBOL>")
            return
        run_script("scripts/llm_workflow.py", ["export", args.ticker.upper()])
    elif args.command == "llm-import":
        run_script("scripts/llm_workflow.py", ["import"])

if __name__ == "__main__":
    main()
