import sys
import os
import argparse
import subprocess

def run_script(script_path, args=[]):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(root_dir, script_path)
    if not os.path.exists(full_path):
        print(f"Error: Could not find script at {full_path}")
        sys.exit(1)
        
    cmd = [sys.executable, full_path] + args
    cwd = os.path.dirname(full_path)
    
    try:
        # Run process, passing stdout and stderr through to console
        subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Process failed with exit code: {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\nProcess cancelled by user.")
        sys.exit(1)

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
    
    # 7. All
    parser_all = subparsers.add_parser("all", help="Regenerate EVERYTHING (Run all 4 modules fully)")
    parser_all.add_argument("--months", type=int, default=1, help="Lookback months for scanners (default: 1)")
    
    args = parser.parse_args()
    
    if args.command == "catalysts":
        print("\n=== Generating ASX Catalyst Radar ===")
        run_script("asx_catalysts/asx_catalysts.py")
        print("=== Complete! Outputs saved to /output/ ===\n")
        
    elif args.command == "analyzer":
        print("\n=== Running ASX Trend Analyzer ===")
        run_script("asx_analyzer/asx_analyzer.py")
        print("=== Complete! Outputs saved to /output/ ===\n")
        
    elif args.command == "announcements":
        print("\n=== Scanning Price Sensitive Announcements ===")
        pass_args = []
        if args.months: pass_args.extend(["--months", str(args.months)])
        if args.no_pdf: pass_args.append("--no-pdf")
        if args.full_refresh: pass_args.append("--full-refresh")
        
        run_script("asx_announcements/asx_announcements.py", pass_args)
        print("=== Complete! Outputs saved to /output/ ===\n")
        
    elif args.command == "placements":
        print("\n=== Scanning Capital Placements ===")
        pass_args = []
        if args.months: pass_args.extend(["--months", str(args.months)])
        if args.no_pdf: pass_args.append("--no-pdf")
        if args.full_refresh: pass_args.append("--full-refresh")
        
        run_script("asx_placements/asx_placements.py", pass_args)
        print("=== Complete! Outputs saved to /output/ ===\n")
        
    elif args.command == "all":
        print("\n" + "="*50)
        print("RUNNING COMPLETE ASX ANALYSIS SUITE")
        print("="*50)
        
        # 1. Catalysts
        print("\n--- [1/4] Catalysts ---")
        run_script("asx_catalysts/asx_catalysts.py")
        
        # 2. Analyzer
        print("\n--- [2/4] Analyzer ---")
        run_script("asx_analyzer/asx_analyzer.py")
        
        # 3. Announcements
        print("\n--- [3/4] Announcements ---")
        scan_args = ["--months", str(args.months)]
        run_script("asx_announcements/asx_announcements.py", scan_args)
        
        # 4. Placements
        print("\n--- [4/4] Placements ---")
        run_script("asx_placements/asx_placements.py", scan_args)
        
        print("\n" + "="*50)
        print("ALL MODULES COMPLETED SUCCESSFULLY")
        print("="*50 + "\n")
        
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
