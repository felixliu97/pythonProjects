import os
import re
import html
from datetime import datetime

# Import the 4 modules
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from asx_analyzer.asx_analyzer import ASXTrendingStocks
from asx_catalysts import asx_catalysts
from asx_announcements import asx_announcements
from asx_placements import asx_placements

def extract_fragment(html_content, module_id):
    """
    Extracts style, script, and body content from a full HTML document.
    Wraps body content in a module-specific div to avoid selector conflicts.
    """
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

def generate_dashboard():
    print("\n" + "="*50)
    print("GENERATING UNIFIED ASX DASHBOARD")
    print("="*50)
    
    # 1. Generate/Fetch HTML from all 4 modules
    print("--- [1/4] Running Analyzer ---")
    analyzer = ASXTrendingStocks()
    analyzer_data = analyzer.get_trending_stocks()
    html_analyzer = analyzer.generate_html_report(analyzer_data, save_file=True)
    
    print("--- [2/4] Running Catalysts ---")
    html_catalysts = asx_catalysts.generate_html(save_file=True)
    
    print("--- [3/4] Running Announcements ---")
    # Note: announcements and placements usually need args, 
    # but here we'll assume they just generate from existing YAML or defaults
    html_announcements = asx_announcements.generate_html(save_file=True)
    
    print("--- [4/4] Running Placements ---")
    html_placements = asx_placements.generate_html(save_file=True)
    
    # 2. Extract fragments
    f_analyzer = extract_fragment(html_analyzer, "analyzer")
    f_catalysts = extract_fragment(html_catalysts, "catalysts")
    f_announcements = extract_fragment(html_announcements, "announcements")
    f_placements = extract_fragment(html_placements, "placements")
    
    # 3. Merge Style & Script
    all_styles = f_analyzer['style'] + f_catalysts['style'] + f_announcements['style'] + f_placements['style']
    all_scripts = f_analyzer['script'] + f_catalysts['script'] + f_announcements['script'] + f_placements['script']
    
    # 4. Render Master Template
    template_path = os.path.join(os.path.dirname(__file__), "templates", "asx_dashboard.html")
    if not os.path.exists(template_path):
        print(f"Error: Master template not found at {template_path}")
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
                         
    output_path = os.path.join(os.path.dirname(__file__), "output", "asx_dashboard.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)
        
    print("\n" + "="*50)
    print(f"DASHBOARD GENERATED: {output_path}")
    print("="*50 + "\n")

if __name__ == "__main__":
    generate_dashboard()
