import sys
import os
import argparse
import subprocess
import json
import yaml
import shutil
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

class C:
    RESET  = '\033[0m'; BOLD = '\033[1m'; DIM = '\033[2m'
    RED = '\033[91m'; GREEN = '\033[92m'; YELLOW = '\033[93m'
    BLUE = '\033[94m'; CYAN = '\033[96m'

def section(msg):  print(f"\n{C.BOLD}{C.CYAN}{msg}{C.RESET}")
def step(msg):     print(f"{C.BOLD}{C.BLUE}{msg}{C.RESET}")
def ok(msg):       print(f"{C.GREEN}{msg}{C.RESET}")
def warn(msg):     print(f"{C.YELLOW}{msg}{C.RESET}")
def err(msg):      print(f"{C.BOLD}{C.RED}{msg}{C.RESET}")

def run_script(script_path, args=[]):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(root_dir, script_path)
    if not os.path.exists(full_path):
        err(f"Error: Could not find script at {full_path}")
        return False
        
    cmd = [sys.executable, full_path] + args
    cwd = os.path.dirname(full_path)
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
        return True
    except Exception as e:
        err(f"Execution failed: {e}")
        return False

def load_json_data(module_name):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(root_dir, "output", f"asx_{module_name}.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

def load_settings():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    settings_path = os.path.join(root_dir, "config", "settings.yaml")
    if os.path.exists(settings_path):
        with open(settings_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

def generate_dashboard():
    section("=== Generating Dashboard ===")
    step("Generating modern Jinja2 dashboard...")
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load settings
    settings = load_settings()

    # 1. Load data from all modules
    data = {
        'analyzer': load_json_data("analyzer"),
        'catalysts': load_json_data("catalysts"),
        'announcements': load_json_data("announcements"),
        'placements': load_json_data("placements"),
        'settings': settings,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # 2. Setup Jinja2
    template_dir = os.path.join(root_dir, "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    
    try:
        # 3. Ensure assets are propagated
        css_src = os.path.join(template_dir, "base.css")
        css_dst = os.path.join(root_dir, "output", "base.css")
        if os.path.exists(css_src):
            shutil.copy(css_src, css_dst)
            
        template = env.get_template("asx_dashboard.html")
        output_html = template.render(**data)
        
        output_path = os.path.join(root_dir, "output", "asx_dashboard.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_html)
        ok(f"Generated {output_path} successfully.")
    except Exception as e:
        err(f"Template rendering failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="ASX Project v1.0 Runner")
    subparsers = parser.add_subparsers(dest="command")
    
    subparsers.add_parser("catalysts")
    ana_p = subparsers.add_parser("analyzer")
    ana_p.add_argument("--force", action="store_true", help="Bypass cache")
    
    ann_p = subparsers.add_parser("announcements")
    ann_p.add_argument("--months", type=int, default=1)
    ann_p.add_argument("--no-pdf", action="store_true")
    
    plac_p = subparsers.add_parser("placements")
    plac_p.add_argument("--months", type=int, default=1)
    
    subparsers.add_parser("dashboard")
    
    all_p = subparsers.add_parser("all")
    all_p.add_argument("--months", type=int, default=1)
    all_p.add_argument("--no-pdf", action="store_true")
    all_p.add_argument("--force", action="store_true", help="Bypass cache")
    
    args = parser.parse_args()
    
    if args.command == "catalysts":
        if run_script("asx_catalysts/asx_catalysts.py"):
            generate_dashboard()
    elif args.command == "analyzer":
        analyzer_args = ["--force"] if args.force else []
        if run_script("asx_analyzer/asx_analyzer.py", analyzer_args):
            generate_dashboard()
    elif args.command == "announcements":
        ann_args = ["--months", str(args.months)]
        if args.no_pdf: ann_args.append("--no-pdf")
        if run_script("asx_announcements/asx_announcements.py", ann_args):
            generate_dashboard()
    elif args.command == "placements":
        if run_script("asx_placements/asx_placements.py", ["--months", str(args.months)]):
            generate_dashboard()
    elif args.command == "dashboard":
        generate_dashboard()
    elif args.command == "all":
        section("=== Full Pipeline Run ===")
        run_script("asx_catalysts/asx_catalysts.py")
        
        analyzer_args = ["--force"] if args.force else []
        run_script("asx_analyzer/asx_analyzer.py", analyzer_args)
        
        ann_args = ["--months", str(args.months)]
        if args.no_pdf: ann_args.append("--no-pdf")
        run_script("asx_announcements/asx_announcements.py", ann_args)
        
        run_script("asx_placements/asx_placements.py", ["--months", str(args.months)])
        generate_dashboard()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
