"""
ASX Research Pipeline - Main Orchestrator (Refactored)

Central entry point for the ASX research pipeline.
Handles scraping, analysis, and UI generation.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

# Force UTF-8 for Windows Terminal compatibility
if sys.stdout.encoding != "utf-8":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Local Imports
try:
    from scripts.schemas import validate_catalyst_records
    from scripts.utils import generate_sparkline, get_root_dir, get_sydney_time, load_yaml_data, logger
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), "scripts"))
    from schemas import validate_catalyst_records
    from utils import generate_sparkline, get_root_dir, get_sydney_time, load_yaml_data, logger


def trim_zeros(value):
    """Jinja2 filter to trim trailing zeros from floats, max 4 decimals."""
    if value is None or value == "":
        return ""
    try:
        f_val = float(value)
        # Force round to 4 decimals first
        s = f"{f_val:.4f}"
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s
    except (ValueError, TypeError):
        return str(value)


# Color Constants
class Color:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def run_script(script: str, args: list[str] | None = None) -> bool:
    """Execute a Python script relative to the root directory."""
    root_dir = get_root_dir()
    full_path = root_dir / script
    if not full_path.exists():
        logger.error(f"Script not found: {full_path}")
        return False

    cmd = [sys.executable, str(full_path)] + (args or [])
    # Only print the script basename and arguments for a cleaner look
    script_display = f"{Path(script).name} {' '.join(args)}" if args else Path(script).name
    print(f"{Color.CYAN}{Color.BOLD}Running:{Color.RESET} {Color.BLUE}{script_display}{Color.RESET}")
    try:
        subprocess.run(cmd, cwd=str(root_dir), check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Execution failed for {script}: {e}")
        return False


def clean_pycache(root_dir: Path) -> None:
    cache_dirs = [
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".hypothesis",
    ]

    for cache_dir_name in cache_dirs:
        for d in root_dir.rglob(cache_dir_name):
            if d.is_dir():
                shutil.rmtree(d, ignore_errors=True)

    for f in root_dir.rglob("*.pyc"):
        if f.is_file():
            try:
                f.unlink()
            except OSError:
                pass

    for f in root_dir.rglob("*.pyo"):
        if f.is_file():
            try:
                f.unlink()
            except OSError:
                pass


def prune_pdf_cache(root_dir: Path) -> None:
    """Keep only announcement PDFs for the latest available trading day in .pdf_cache."""
    cache_dir = root_dir / ".pdf_cache"
    if not cache_dir.exists() or not cache_dir.is_dir():
        return

    try:
        ann = load_yaml_data("asx_announcements.yaml")
        if not ann:
            return

        latest_date_str = max([str(a.get("Date", "")) for a in ann])
        if not latest_date_str:
            return
    except Exception as e:
        logger.error(f"Failed to determine latest announcement date for PDF cache pruning: {e}")
        return

    keep_date = latest_date_str
    removed = 0

    for file_path in cache_dir.iterdir():
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() != ".pdf":
            continue

        match = re.match(r"^(\d{4}-\d{2}-\d{2})_", file_path.name)
        if not match:
            try:
                file_path.unlink()
                removed += 1
            except OSError as e:
                logger.warning(f"Failed to remove unrecognized cached PDF {file_path.name}: {e}")
            continue

        file_date = match.group(1)
        if file_date != keep_date:
            try:
                file_path.unlink()
                removed += 1
            except OSError as e:
                logger.warning(f"Failed to remove cached PDF {file_path.name}: {e}")

    if removed:
        logger.info(f"Pruned .pdf_cache to latest trading day {keep_date}; removed {removed} stale PDFs.")


def load_catalysts_from_yaml() -> list:
    """Load catalyst data directly from YAML (single source of truth)."""
    yaml_path = get_root_dir() / "config" / "asx_catalysts.yaml"
    with open(yaml_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or []

    validated_records = validate_catalyst_records(raw)

    catalysts_list = []
    for validated_entry in validated_records:
        catalysts_list.append(
            {
                "Ticker": validated_entry.Ticker,
                "Stage": validated_entry.Stage,
                "Company": validated_entry.Company,
                "Sector": validated_entry.Sector or "",
                "Rating": validated_entry.Rating,
                "Catalysts": validated_entry.Catalysts,
                "Risks": validated_entry.Risks,
                "CR_Risk": validated_entry.CR_Risk,
                "CR_Risk_Reason": validated_entry.CR_Risk_Reason,
                "Breakout_Probability": validated_entry.Breakout_Probability,
                "Breakout_Probability_Reason": validated_entry.Breakout_Probability_Reason,
                "Core_Notes": validated_entry.Core_Notes,
                "Timeline": sorted(validated_entry.Timeline, key=lambda x: str(x.get("Date", ""))),
            }
        )
    return catalysts_list


def load_data() -> dict:
    """Fetch consolidated data: catalysts, announcements, placements, market trends from YAML."""
    # 1. Catalyst Data (from YAML directly)
    catalysts_list = load_catalysts_from_yaml()

    # Sort catalysts by rating/breakout/cr_risk
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

    # 4. Market Trends (Categorized for Template)
    trends = load_yaml_data("asx_market_trends.yaml")
    analyzer_data = {"growth_stocks": [], "foundation_stocks": [], "etfs": [], "global_timeline": []}

    trend_lookup = {t["symbol"]: t for t in trends if "symbol" in t}

    for t in trends:
        s_obj = {
            "symbol": t.get("symbol"),
            "name": t.get("name"),
            "industry": t.get("industry"),
            "current_price": t.get("current_price") or 0.0,
            "marketCap": t.get("market_cap") or 0,
            "pe": t.get("pe"),
            "yield": t.get("yield_val") or 0.0,
            "score": t.get("score") or 0.0,
            "price_change_1d": t.get("price_change_1d") or 0.0,
            "price_diff_1d": t.get("price_diff_1d") or 0.0,
            "price_change_5d": t.get("price_change_5d") or 0.0,
            "price_diff_5d": t.get("price_diff_5d") or 0.0,
            "momentum": t.get("momentum") or 0.0,
            "volatility": t.get("volatility") or 0.0,
            "volume_change": t.get("volume_change") or 0.0,
            "rsi": t.get("rsi") or 50.0,
            "sparkline": generate_sparkline(t.get("price_history")),
        }
        stype = t.get("stock_type", "growth")
        if stype == "growth":
            analyzer_data["growth_stocks"].append(s_obj)
        elif stype == "foundation":
            analyzer_data["foundation_stocks"].append(s_obj)
        elif stype == "etf":
            analyzer_data["etfs"].append(s_obj)

    # 2. Announcements
    ann = load_yaml_data("asx_announcements.yaml")
    latest_date_str = max([str(a.get("Date", "")) for a in ann]) if ann else ""

    ann_res = [a for a in ann if str(a.get("Date", "")) == latest_date_str]
    ann_res.sort(key=lambda x: x.get("Rating", 0), reverse=True)

    ann_list = []
    for a in ann_res:
        sym = a.get("ASX_Code")
        trend = trend_lookup.get(sym)
        ann_list.append(
            {
                "ASX_Code": sym,
                "Company": a.get("Company"),
                "Headline": a.get("Headline"),
                "Date": a.get("Date", ""),
                "Summary": a.get("Summary"),
                "PDF_Link": a.get("PDF_Link"),
                "Rating": a.get("Rating") or 0,
                "Current_Price": trend.get("current_price") if trend else None,
                "Price_Change_1d": trend.get("price_change_1d") or 0.0 if trend else 0.0,
                "Price_Diff_1d": trend.get("price_diff_1d") or 0.0 if trend else 0.0,
                "RSI": trend.get("rsi") if trend else 50.0,
            }
        )

    # 3. Placements
    plac_res = load_yaml_data("asx_placements.yaml")
    plac_res.sort(key=lambda x: str(x.get("Date", "")), reverse=True)
    plac_res = plac_res[:150]

    plac_list = [
        {
            "ASX_Code": p.get("ASX_Code"),
            "Company": p.get("Company"),
            "Headline": p.get("Headline"),
            "Date": p.get("Date", ""),
            "CR_Price": p.get("CR_Price"),
            "Current_Price": p.get("Current_Price"),
            "Price_Diff_%": p.get("Price_Diff_%") or 0.0,
            "PDF_Link": p.get("PDF_Link"),
        }
        for p in plac_res
    ]

    return {
        "analyzer": analyzer_data,
        "catalysts": {"catalysts": catalysts_list},
        "announcements": {"announcements": ann_list},
        "placements": {"placements": plac_list},
        "timestamp": get_sydney_time().strftime("%Y-%m-%d %H:%M:%S"),
    }


def build_dashboard():
    """Render the dashboard using Jinja2 templates."""
    logger.info("Generating Dashboard HTML...")
    root_dir = get_root_dir()
    template_dir = root_dir / "templates"
    output_path = root_dir / "output" / "asx_dashboard.html"

    # Ensure output directory exists
    output_path.parent.mkdir(exist_ok=True)

    data = load_data()

    env = Environment(loader=FileSystemLoader(str(template_dir)))
    env.filters["trim_zeros"] = trim_zeros

    template = env.get_template("asx_dashboard.html")

    html_content = template.render(**data)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Copy static assets (base.css) from templates to output
    css_src = template_dir / "base.css"
    if css_src.exists():
        shutil.copy2(css_src, output_path.parent / "base.css")

    print(
        f"{Color.GREEN}{Color.BOLD}✨ Dashboard successfully updated:{Color.RESET} "
        f"{Color.BLUE}{output_path.name}{Color.RESET}"
    )


def run_integrity_check():
    """Run pytest prerequisites before allowing data operations."""
    print(f"{Color.YELLOW}{Color.BOLD}🛡️  Running pytest pre-requisite checks...{Color.RESET}")

    env = os.environ.copy()
    env["TESTING"] = "true"

    try:
        # Run pytest via module to ensure correct path resolution
        cmd = [sys.executable, "-m", "pytest", "tests", "-q", "--no-summary"]
        subprocess.run(cmd, env=env, check=True)
        print(f"{Color.GREEN}{Color.BOLD}✅ Pytest pre-requisite passed.{Color.RESET}")
        return True
    except subprocess.CalledProcessError:
        print(
            f"{Color.RED}{Color.BOLD}❌ Pytest pre-requisite FAILED. "
            f"Please fix the test suite before running.{Color.RESET}"
        )
        # Run again without -q to show the actual errors
        subprocess.run([sys.executable, "-m", "pytest", "tests"], env=env)
        return False


def should_skip_data_pull():
    """Returns True if it's weekend and YAML already has latest Friday data."""
    now = get_sydney_time()
    # 5 is Saturday, 6 is Sunday
    if now.weekday() not in [5, 6]:
        return False

    try:
        ann = load_yaml_data("asx_announcements.yaml")
        if not ann:
            return False

        latest_date_str = max([str(a.get("Date", "")) for a in ann])
        if not latest_date_str:
            return False

        latest_date = datetime.strptime(latest_date_str, "%Y-%m-%d").date()

        # Target is the most recent Friday
        days_since_friday = 1 if now.weekday() == 5 else 2
        friday_date = (now - timedelta(days=days_since_friday)).date()

        if latest_date >= friday_date:
            print(
                f"{Color.YELLOW}{Color.BOLD}🛌 Weekend mode active. "
                f"Data is already up-to-date (Latest: {latest_date}). "
                f"Skipping pull/analyze...{Color.RESET}"
            )
            return True
    except Exception as e:
        logger.error(f"Error checking weekend skip logic: {e}")
    return False


def main():
    parser = argparse.ArgumentParser(description="ASX Research Hub Control Center")
    parser.add_argument(
        "command",
        choices=["all", "scrape", "analyze", "dashboard"],
        help="Pipeline command to run",
    )
    parser.add_argument("--force", action="store_true", help="Force a full refresh (ignore incremental sync)")
    # cache cleanup runs automatically after every command
    args = parser.parse_args()

    # Shared flags for scrapers
    scrape_args = ["--full-refresh"] if args.force else []

    root_dir = get_root_dir()
    exit_code = 0
    try:
        if args.command == "scrape":
            ok1 = run_script("scripts/asx_announcements.py", scrape_args)
            ok2 = run_script("scripts/asx_placements.py", scrape_args)
            if not (ok1 and ok2):
                exit_code = 1
        elif args.command == "analyze":
            if not run_integrity_check():
                sys.exit(1)
            ok = run_script("scripts/asx_analyzer.py")
            if not ok:
                exit_code = 1
        elif args.command == "dashboard":
            try:
                build_dashboard()
            except Exception as e:
                logger.error(f"Dashboard build failed: {e}")
                exit_code = 1
        elif args.command == "all":
            if not run_integrity_check():
                sys.exit(1)

            skip_pull = should_skip_data_pull() and not args.force

            ok1, ok2, ok3 = True, True, True
            if not skip_pull:
                ok1 = run_script("scripts/asx_announcements.py", scrape_args)
                ok2 = run_script("scripts/asx_placements.py", scrape_args)
                # Analyze symbols from the latest available announcement date
                ann_syms = []
                try:
                    ann = load_yaml_data("asx_announcements.yaml")
                    if ann:
                        latest_date_str = max([str(a.get("Date", "")) for a in ann])
                        ann_syms = list(
                            {
                                a.get("ASX_Code")
                                for a in ann
                                if str(a.get("Date", "")) == latest_date_str and a.get("ASX_Code")
                            }
                        )
                except Exception as e:
                    logger.error(f"Failed to fetch latest announcement symbols: {e}")
                    pass
                analyzer_args = ["--extra-symbols", ",".join(ann_syms)] if ann_syms else []
                ok3 = run_script("scripts/asx_analyzer.py", analyzer_args)

            if not (ok1 and ok2 and ok3):
                exit_code = 1
            try:
                build_dashboard()
            except Exception as e:
                logger.error(f"Dashboard build failed: {e}")
                exit_code = 1
    finally:
        prune_pdf_cache(root_dir)
        clean_pycache(root_dir)

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
