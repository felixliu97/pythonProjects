import sys
import os
import argparse
import subprocess
import re
import html
from datetime import datetime

class C:
    RESET  = '\033[0m'
    BOLD   = '\033[1m'
    DIM    = '\033[2m'
    RED    = '\033[91m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    BLUE   = '\033[94m'
    CYAN   = '\033[96m'

def section(msg):  print(f"\n{C.BOLD}{C.CYAN}{msg}{C.RESET}")
def step(msg):     print(f"{C.BOLD}{C.BLUE}{msg}{C.RESET}")
def ok(msg):       print(f"{C.GREEN}{msg}{C.RESET}")
def warn(msg):     print(f"{C.YELLOW}{msg}{C.RESET}")
def err(msg):      print(f"{C.BOLD}{C.RED}{msg}{C.RESET}")
def dim(msg):      print(f"{C.DIM}{msg}{C.RESET}")

def run_script(script_path, args=[]):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(root_dir, script_path)
    if not os.path.exists(full_path):
        err(f"Error: Could not find script at {full_path}")
        sys.exit(1)
        
    cmd = [sys.executable, full_path] + args
    cwd = os.path.dirname(full_path)
    
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        err(f"Process failed with exit code: {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        warn("\nProcess cancelled by user.")
        sys.exit(1)

def extract_fragment(html_content, module_id):
    """
    Extracts style, script, and body content from a full HTML document.
    Wraps body content in a module-specific div to avoid selector conflicts.
    """
    if not html_content:
        return {'body': '', 'style': '', 'script': ''}
        
    # 1. Extract Body (everything inside <body>...</body>)
    body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
    body = body_match.group(1) if body_match else html_content
    
    # Remove the onload attribute if present (we'll handle it manually)
    body = re.sub(r'onload=".*?"', '', body)
    
    # 2. Extract Styles
    styles = re.findall(r'<style[^>]*>(.*?)</style>', html_content, re.DOTALL | re.IGNORECASE)
    style_content = "\n".join(styles)
    
    # 3. Extract Scripts
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html_content, re.DOTALL | re.IGNORECASE)
    script_content = "\n".join(scripts)
    
    # Wrap body to isolate (optional, but helps)
    wrapped_body = f'<div id="module-{module_id}" class="module-wrap">{body}</div>'
    
    return {
        'body': wrapped_body,
        'style': style_content,
        'script': script_content
    }

def get_report_html(module_name):
    """Reads the generated HTML for a module from the output directory."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    report_path = os.path.join(root_dir, "output", f"asx_{module_name}.html")
    
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            return f.read()
    
    warn(f"Warning: Could not find report for {module_name} at {report_path}")
    return f'<div class="error">Report for {module_name} not found. Run "run.py {module_name}" first.</div>'

def generate_dashboard():
    dim("Generating unified dashboard...")
    
    # 1. Fetch HTML from all 4 modules
    html_analyzer = get_report_html("analyzer")
    html_catalysts = get_report_html("catalysts")
    html_announcements = get_report_html("announcements")
    html_placements = get_report_html("placements")
    
    # 2. Extract fragments
    f_analyzer = extract_fragment(html_analyzer, "analyzer")
    f_catalysts = extract_fragment(html_catalysts, "catalysts")
    f_announcements = extract_fragment(html_announcements, "announcements")
    f_placements = extract_fragment(html_placements, "placements")
    
    # 3. Merge Style & Script
    all_styles = f_analyzer['style'] + f_catalysts['style'] + f_announcements['style'] + f_placements['style']
    all_scripts = f_analyzer['script'] + f_catalysts['script'] + f_announcements['script'] + f_placements['script']
    
    # 4. Render Master Template
    root_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(root_dir, "templates", "asx_dashboard.html")
    if not os.path.exists(template_path):
        err(f"Error: Master template not found at {template_path}")
        return
        
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
        
    final_html = template.replace("{{ analyzer_content }}", f_analyzer['body'])\
                         .replace("{{ catalysts_content }}", f_catalysts['body'])\
                         .replace("{{ announcements_content }}", f_announcements['body'])\
                         .replace("{{ placements_content }}", f_placements['body'])\
                         .replace("{{ master_styles }}", all_styles)\
                         .replace("{{ master_scripts }}", all_scripts)\
                         .replace("{{ timestamp }}", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                         
    output_path = os.path.join(root_dir, "output", "asx_dashboard.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)
        
    ok(f"Generated {output_path} successfully.")

def main():
    parser = argparse.ArgumentParser(description="ASX Project Unified CLI Runner", formatter_class=argparse.RawTextHelpFormatter)
    
    subparsers = parser.add_subparsers(dest="command", help="Module to run")
    
    # 1. Catalysts
    parser_catalysts = subparsers.add_parser("catalysts", help="Generate fundamental Catalysts Radar (HTML)")
    
    # 2. Analyzer
    parser_analyzer = subparsers.add_parser("analyzer", help="Run Technical Trend Analyzer (HTML)")
    
    # 3. Announcements
    parser_ann = subparsers.add_parser("announcements", help="Scan for Price Sensitive Announcements (YAML + HTML)")
    parser_ann.add_argument("--months", type=int, default=2, help="Lookback months (default: 2)")
    parser_ann.add_argument("--no-pdf", action="store_true", help="Skip PDF download & extraction")
    parser_ann.add_argument("--full-refresh", action="store_true", help="Ignore existing database; full re-scan")
    
    # 4. Placements
    parser_plac = subparsers.add_parser("placements", help="Scan for Placements / Capital Raisings (YAML + HTML)")
    parser_plac.add_argument("--months", type=int, default=2, help="Lookback months (default: 2)")
    parser_plac.add_argument("--no-pdf", action="store_true", help="Skip PDF download & extraction")
    parser_plac.add_argument("--full-refresh", action="store_true", help="Ignore existing database; full re-scan")
    
    # Dashboard
    parser_dash = subparsers.add_parser("dashboard", help="Generate Unified Dashboard (HTML)")
    
    # 7. All
    parser_all = subparsers.add_parser("all", help="Regenerate EVERYTHING (Run all 4 modules fully)")
    parser_all.add_argument("--months", type=int, default=1, help="Lookback months for scanners (default: 1)")
    
    args = parser.parse_args()
    
    if args.command == "catalysts":
        section("=== Catalysts ===")
        run_script("asx_catalysts/asx_catalysts.py")
        
    elif args.command == "analyzer":
        section("=== Analyzer ===")
        run_script("asx_analyzer/asx_analyzer.py")
        
    elif args.command == "announcements":
        section("=== Announcements ===")
        pass_args = []
        if args.months: pass_args.extend(["--months", str(args.months)])
        if args.no_pdf: pass_args.append("--no-pdf")
        if args.full_refresh: pass_args.append("--full-refresh")
        run_script("asx_announcements/asx_announcements.py", pass_args)
        
    elif args.command == "placements":
        section("=== Placements ===")
        pass_args = []
        if args.months: pass_args.extend(["--months", str(args.months)])
        if args.no_pdf: pass_args.append("--no-pdf")
        if args.full_refresh: pass_args.append("--full-refresh")
        run_script("asx_placements/asx_placements.py", pass_args)
        
    elif args.command == "dashboard":
        section("=== Dashboard (Regenerate from cache) ===")
        step("--- [1/5] Catalysts ---")
        run_script("asx_catalysts/asx_catalysts.py")
        step("--- [2/5] Analyzer ---")
        run_script("asx_analyzer/asx_analyzer.py", ["--html-only"])
        step("--- [3/5] Announcements ---")
        run_script("asx_announcements/asx_announcements.py", ["--html-only"])
        step("--- [4/5] Placements ---")
        run_script("asx_placements/asx_placements.py", ["--html-only"])
        step("--- [5/5] Dashboard ---")
        generate_dashboard()
        
    elif args.command == "all":
        section("=== Full Analysis Suite (Full Refresh) ===")
        step("--- [1/5] Catalysts ---")
        run_script("asx_catalysts/asx_catalysts.py")
        step("--- [2/5] Analyzer ---")
        run_script("asx_analyzer/asx_analyzer.py", ["--quiet"])
        step("--- [3/5] Announcements ---")
        scan_args = ["--months", str(args.months)]
        run_script("asx_announcements/asx_announcements.py", scan_args)
        step("--- [4/5] Placements ---")
        run_script("asx_placements/asx_placements.py", scan_args)
        step("--- [5/5] Dashboard ---")
        generate_dashboard()
        ok("Done.")
        
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
