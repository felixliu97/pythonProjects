import pytest
import base64
from jinja2 import Environment
from scripts.utils import generate_sparkline
from run import trim_zeros

# --- 0. trim_zeros Filter ---

def test_trim_zeros_4_decimal_precision():
    """trim_zeros should preserve up to 4 decimal places and strip trailing zeros."""
    assert trim_zeros(0.7625) == "0.7625"    # 4 decimals preserved
    assert trim_zeros(0.125) == "0.125"       # 3 decimals preserved
    assert trim_zeros(1.50) == "1.5"          # trailing zeros stripped
    assert trim_zeros(2.0) == "2"             # integer-like
    assert trim_zeros(0.0325) == "0.0325"     # 4 decimals preserved
    assert trim_zeros(None) == ""
    assert trim_zeros("") == ""


# --- 1. Visual Formatting Logic (Dashboard) ---

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

# --- 2. Sparkline Generation (Integrated in Run) ---

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

def test_timeline_sorting():
    """Verify that timeline items loaded from YAML are sorted by the 'Time' field."""
    import yaml
    from unittest.mock import patch
    from run import load_catalysts_from_yaml
    
    yaml_content = [{
        "Ticker": "TEST", "Company": "Test Co", "Sector": "Tech",
        "CR_Risk": "Low", "Breakout_Probability": "High", "Core_Notes": "",
        "Rating": "观望",
        "Timeline": [
            {"Time": "2026-04-10", "Event": "Event 2"},
            {"Time": "2026-03-20", "Event": "Event 1"},
            {"Time": "2026-05-01", "Event": "Event 3"},
        ]
    }]
    
    def mock_open_yaml(*a, **kw):
        from io import StringIO
        return StringIO(yaml.dump(yaml_content, allow_unicode=True))
    
    with patch("builtins.open", mock_open_yaml):
        result = load_catalysts_from_yaml()
        timeline = result[0]["Timeline"]
        
        assert timeline[0]["Time"] == "2026-03-20"
        assert timeline[1]["Time"] == "2026-04-10"
        assert timeline[2]["Time"] == "2026-05-01"


def test_catalysts_from_yaml_defaults():
    """Verify that missing YAML fields get sensible defaults."""
    import yaml
    from unittest.mock import patch
    from run import load_catalysts_from_yaml
    
    yaml_content = [{"Ticker": "MIN", "Company": "Minimal Co"}]
    
    def mock_open_yaml(*a, **kw):
        from io import StringIO
        return StringIO(yaml.dump(yaml_content, allow_unicode=True))
    
    with patch("builtins.open", mock_open_yaml):
        result = load_catalysts_from_yaml()
        c = result[0]
        assert c["Ticker"] == "MIN"
        assert c["Rating"] == "观望"
        assert c["CR_Risk"] == "Unknown"
        assert c["Breakout_Probability"] == "N/A"
        assert c["Timeline"] == []
        assert c["Catalysts"] == []
        assert c["Risks"] == []
