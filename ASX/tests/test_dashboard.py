import pytest
import base64
from jinja2 import Environment
from scripts.utils import generate_sparkline

# --- 1. Visual Formatting Logic ---

def test_pe_negative_logic():
    """Verify that negative P/E values are handled correctly as '-'."""
    env = Environment()
    template_str = '{{ "%.1f"|format(s.pe) if (s.pe is number and s.pe > 0) else "-" }}'
    template = env.from_string(template_str)
    
    assert template.render(s={"pe": 15.6}) == "15.6"
    assert template.render(s={"pe": -5.0}) == "-"
    assert template.render(s={"pe": 0}) == "-"
    assert template.render(s={"pe": None}) == "-"

def test_price_change_format_logic():
    """Verify that price change formatting and sorting logic works."""
    env = Environment()
    env.filters['trim_zeros'] = lambda x: str(x)
    
    template_str = (
        '<span style="display:none">{{ "%010.3f"|format((s.price_diff_1d|default(0)) + 10000.0) }}</span>'
        '{{ s.price_change_1d|trim_zeros }} ({{ "%+ .2f"|format(s.price_diff_1d) }}%)'
    )
    template = env.from_string(template_str)
    
    # Text part: 0.05 (+1.25%)
    # Sort part: %010.3f format of 10001.25 -> 10001.250
    res = template.render(s={"price_change_1d": 0.05, "price_diff_1d": 1.25})
    assert "0.05 (+1.25%)" in res
    assert "10001.250" in res

# --- 2. Sparkline Generation ---

def test_sparkline_trend_colors():
    """Verify that sparklines are colored based on the price trend."""
    up_prices = "1.0,1.1,1.2"
    down_prices = "1.2,1.1,1.0"
    
    def get_svg_content(data_uri):
        if not data_uri: return ""
        b64_part = data_uri.split(",")[1]
        return base64.b64decode(b64_part).decode()

    # Green for Up (#00C853)
    svg_up = get_svg_content(generate_sparkline(up_prices))
    assert 'stroke="#00C853"' in svg_up
    
    # Red for Down (#FF5252)
    svg_down = get_svg_content(generate_sparkline(down_prices))
    assert 'stroke="#FF5252"' in svg_down

# --- 3. Link generation ---

def test_announcement_link_logic():
    """Verify that PDF links are generated correctly."""
    env = Environment()
    template_str = '<a href="{{ s.pdf_link }}">Link</a>'
    template = env.from_string(template_str)
    
    res = template.render(s={"pdf_link": "https://asx.com.au/pdf/123"})
    assert "href=\"https://asx.com.au/pdf/123\"" in res
