import yaml
import os
import html
import re
from datetime import datetime

# Current reference date for "past" vs "future"
TODAY = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

# Paths
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(ROOT_DIR, "stocks.yaml")
HTML_OUT = os.path.join(ROOT_DIR, "asx_catalyst_radar_6mo.html")

def get_class_for_probability(prob):
    if not prob: return "p-med", 50, "#FBC02D"
    p = prob.strip()
    if p.startswith("极高"): return "p-vhigh", 95, "#0D47A1"
    if p.startswith("高"): return "p-high", 80, "#2E7D32"
    if p.startswith("中高"): return "p-mhigh", 65, "#C0CA33"
    if p.startswith("中"):
        if p.startswith("中低"): return "p-mlow", 35, "#F57C00"
        return "p-med", 50, "#FBC02D"
    if p.startswith("低"): return "p-low", 20, "#D32F2F"
    return "p-med", 50, "#FBC02D"

def get_sector_class(sector):
    if not sector: return ""
    s = sector.lower()
    if "pgm" in s or "ti" in s or "v" in s: return "s-pgm"
    if "金" in s or "黄金" in s or "锑" in s or "钨" in s: return "s-gold"
    if "铀" in s or "uranium" in s: return "s-uranium"
    if "铜" in s or "copper" in s: return "s-copper"
    if "生物" in s or "energy" in s: return "s-energy"
    if "药" in s or "皮肤" in s or "pharma" in s: return "s-pharma"
    if "石墨" in s or "critical" in s: return "s-critical"
    return ""

def determine_event_pill_class(event_text):
    text = event_text.lower()
    if "重大发现" in text or "已确认" in text or "首气" in text:
        return "e-hot"
    if "钻探" in text or "drill" in text:
        return "e-drill"
    if "融资" in text or "资本" in text or "完成并入" in text or "入股" in text or "mou" in text:
        return "e-corporate"
    if "生产" in text or "稳产" in text:
        return "e-production"
    if "现金流" in text or "风险" in text:
        return "e-risk"
    if "报" in text or "结果" in text or "分析" in text:
        return "e-result"
    return "e-milestone"

def build_row(stock):
    ticker = stock.get("Ticker", "")
    sector = stock.get("Sector", "")
    sec_class = get_sector_class(sector)
    
    # Extra badges/styles for highlight
    ticker_html = f'<div class="ticker">{ticker}</div>'
    row_html = f'<tr>\n'
    
    # 1. Ticker & Sector
    row_html += f'  <td>\n    {ticker_html}\n'
    if sector:
        row_html += f'    <div class="sector-tag {sec_class}">{sector}</div>\n'
    row_html += f'  </td>\n'
    
    # 1.5 Timeline Table Column
    row_html += '  <td>\n'
    timeline = stock.get("Timeline", [])
    if timeline:
        for item in timeline:
            time_label = str(item.get("Time", ""))
            event_label = item.get("Event", "")
            tl_time_cls = "tl-time"
            if "2026" in time_label: tl_time_cls += " tl-future"
            if "即将到来" in time_label: tl_time_cls += " tl-soon"
            row_html += f'    <div class="tl-item"><span class="{tl_time_cls}">{time_label}</span><span>{event_label}</span></div>\n'
    else:
        row_html += '    <span style="color:#ccc;font-size:10px;">-</span>\n'
    row_html += '  </td>\n'
    
    # 2. Catalysts
    row_html += '  <td>\n'
    for cat in stock.get("Catalysts", []):
        cat_str = str(cat)
        pill_cls = determine_event_pill_class(cat_str)
        row_html += f'    <span class="event-pill {pill_cls}">{html.escape(cat_str)}</span>\n'
    row_html += '  </td>\n'
    
    # 2.5 Risks
    row_html += '  <td>\n'
    risks = stock.get("Risks", [])
    if risks:
        for risk in risks:
            row_html += f'    <span class="event-pill e-risk">{risk}</span>\n'
    else:
        row_html += '    <span style="color:#ccc;font-size:10px;">-</span>\n'
    row_html += '  </td>\n'
    
    # 3. Earnings
    row_html += '  <td>\n'
    for earn in stock.get("Earnings_Window", []):
         row_html += f'    <span class="event-pill e-result">{earn}</span>\n'
    row_html += '  </td>\n'
    
    # 4. Heatmap
    row_html += '  <td>\n    <div class="month-bar">\n'
    for ht in stock.get("Heatmap", []):
        st = ht.get("Status", "")
        reason = ht.get("Reason", "")
        mb_cls = "mb"
        if st == "Hot": mb_cls = "mb mb-hot"
        elif st == "Active": mb_cls = "mb mb-active"
        elif st == "Watch": mb_cls = "mb mb-watch"
        row_html += f'      <div class="{mb_cls}" title="{html.escape(reason, quote=True)}"></div>\n'
    row_html += '    </div>\n  </td>\n'
    
    # 5. CR Risk
    row_html += '  <td>\n'
    cr = stock.get("CR_Risk", "")
    
    cr_level = cr.strip()
    cr_desc = ""
    for sep in [" (", " （", "(", "（", " "]:
        if sep in cr_level:
            parts = cr_level.split(sep, 1)
            cr_level = parts[0].strip()
            # Restore parentheses if they were used
            if "(" in sep: cr_desc = "(" + parts[1].strip()
            elif "（" in sep: cr_desc = "（" + parts[1].strip()
            else: cr_desc = parts[1].strip()
            break
            
    lvl_cls = "cr-low"
    if "极高" in cr_level or "高" in cr_level:
        lvl_cls = "cr-high"
    elif "中" in cr_level:
        lvl_cls = "cr-med"
        
    row_html += f'    <div class="cr-val {lvl_cls}">{cr_level}</div>\n'
    if cr_desc:
        row_html += f'    <div class="cr-desc">{cr_desc}</div>\n'
    row_html += '  </td>\n'
    
    # 6. Probability
    prob = stock.get("Probability", "")
    pb_cls, width, bg_color = get_class_for_probability(prob)
    
    row_html += '  <td>\n    <div class="prob">\n'
    row_html += f'      <div class="prob-bar-wrap"><div class="prob-bar" style="width:{width}%; background:{bg_color};"></div></div>\n'
    row_html += f'      <span class="prob-val {pb_cls}">{prob}</span>\n'
    row_html += '    </div>\n  </td>\n'
    
    # 7. Note
    note = stock.get("Core_Notes", "")
    if "⚠" in note:
        parts = note.split("⚠")
        note = parts[0] + '<span class="warn-tag">⚠ ' + parts[1] + '</span>'
    
    # Ensure linebreaks are preserved
    note = note.replace("\n", "<br>")

    row_html += f'  <td>\n    <div class="note-text">{note}</div>\n  </td>\n'
    
    row_html += '</tr>\n'
    return row_html

def generate_html():
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            stocks = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading YAML from {JSON_FILE}: {e}")
        return
            
    def breakout_key(s):
        p = s.get("Probability", "")
        base = 0
        p = p.strip()
        if p.startswith("极高"): base = -6
        elif p.startswith("高"): base = -5
        elif p.startswith("中高"): base = -4
        elif p.startswith("中低"): base = -2
        elif p.startswith("中"): base = -3
        elif p.startswith("低"): base = -1
        
        hot_count = sum(1 for h in s.get("Heatmap", []) if h.get("Status") == "Hot")
        return (base, -hot_count, s.get("Ticker", ""))
        
    stocks.sort(key=breakout_key)

    rows_html = ""
    for s in stocks:
        rows_html += build_row(s)
        rows_html += "\n"
        
    # Build Breakout Ranking HTML
    breakout_html = ""
    # Define color sequence for top 10
    bg_colors = [
        ("#E24B4A", "#4A0808"), ("#E24B4A", "#4A0808"), ("#E24B4A", "#4A0808"), 
        ("#EF9F27", "#412402"), ("#EF9F27", "#412402"), ("#EF9F27", "#412402"),
        ("#1D9E75", "#04342C"), ("#1D9E75", "#04342C"), ("#1D9E75", "#04342C"), ("#1D9E75", "#04342C")
    ]
    
    def get_upcoming_catalyst(cats):
        for cat in cats:
            # Robustly handle if cat is not a string (e.g. from malformed YAML)
            if isinstance(cat, dict):
                # If it's a dict like {'Date': 'Event'}, join them
                cat_str = " ".join([f"{k} {v}" for k, v in cat.items()])
            else:
                cat_str = str(cat)
                
            # Simple heuristic to detect past dates
            # Match YYYY年M月D日 or YYYY-MM-DD
            m1 = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', cat_str)
            m2 = re.search(r'(\d{4})-(\d{2})-(\d{2})', cat_str)
            
            date_found = None
            if m1:
                date_found = datetime(int(m1.group(1)), int(m1.group(2)), int(m1.group(3)))
            elif m2:
                date_found = datetime(int(m2.group(1)), int(m2.group(2)), int(m2.group(3)))
            
            if date_found and date_found < TODAY:
                continue # Skip past event
            return cat_str # Return first non-past event
        return str(cats[0]) if cats else ""

    for i, s in enumerate(stocks[:10]):
        tk = s.get("Ticker", "")
        cats = s.get("Catalysts", [])
        reason = get_upcoming_catalyst(cats)
        bg, col = bg_colors[i] if i < len(bg_colors) else ("#eee", "#333")
        breakout_html += f'      <div style="display:flex; align-items:center; gap:8px; font-size:12px;"><span style="background:{bg}; color:{col}; padding:2px 8px; border-radius:99px; font-size:10px; font-weight:500;">{i+1}</span>{tk} — {reason}</div>\n'

    template_path = os.path.join(ROOT_DIR, "templates", "radar_base_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    final_html = template.replace("{{ table_rows }}", rows_html)\
                         .replace("{{ breakout_html }}", breakout_html)

    with open(HTML_OUT, 'w', encoding='utf-8') as f:
        f.write(final_html)
        
    print(f"Generated {HTML_OUT} successfully with {len(stocks)} stocks.")

if __name__ == "__main__":
    generate_html()
