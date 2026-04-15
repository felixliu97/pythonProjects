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
    """Verify that timeline items are sorted by the 'Time' (Date) field."""
    from run import load_db_data
    from unittest.mock import MagicMock, patch
    
    # Mock database session and data
    mock_catalyst = MagicMock()
    mock_catalyst.symbol = "TEST"
    mock_catalyst.company = "Test Co"
    mock_catalyst.sector = "Tech"
    mock_catalyst.cr_risk = "Low"
    mock_catalyst.cr_risk_reason = ""
    mock_catalyst.breakout_probability = "High"
    mock_catalyst.breakout_probability_reason = ""
    mock_catalyst.core_notes = ""
    
    # Unsorted items (April before March)
    it1 = MagicMock(item_type='milestone', label='2026-04-10', content='Event 2')
    it2 = MagicMock(item_type='milestone', label='2026-03-20', content='Event 1')
    it3 = MagicMock(item_type='milestone', label='2026-05-01', content='Event 3')
    
    with patch("run.db.session_scope") as mock_scope:
        mock_sess = MagicMock()
        mock_scope.return_value.__enter__.return_value = mock_sess
        
        # 1. Mock the symbols query
        mock_sess.query.return_value.all.side_effect = [[mock_catalyst], [it1, it2, it3], [], [], []]
        
        # 2. Mock individual table mocks if needed (but load_db_data uses query(Stock), query(CatalystMaster) etc)
        # We need to simulate the return values for CatalystMaster, Stock, Announcement, Placement, MarketTrend
        # Re-mocking more broadly:
        mock_sess.query.return_value.filter_by.return_value.all.return_value = [it1, it2, it3]
        mock_sess.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        data = load_db_data()
        timeline = data['catalysts']['catalysts'][0]['Timeline']
        
        # Expected: Event 1 (March), Event 2 (April), Event 3 (May)
        assert timeline[0]['Time'] == '2026-03-20'
        assert timeline[1]['Time'] == '2026-04-10'
        assert timeline[2]['Time'] == '2026-05-01'

def test_timeline_merging():
    """Verify that multiple timeline items on the same date are merged and deduplicated."""
    from run import load_db_data
    from unittest.mock import MagicMock, patch
    
    mock_catalyst = MagicMock()
    mock_catalyst.symbol = "TEST"
    mock_catalyst.company = "Test Co"
    mock_catalyst.sector = "Tech"
    mock_catalyst.cr_risk = "Low"
    mock_catalyst.cr_risk_reason = ""
    mock_catalyst.breakout_probability = "High"
    mock_catalyst.breakout_probability_reason = ""
    mock_catalyst.core_notes = ""
    
    # 1. Exact duplicates on same day
    # 2. Different events on same day
    # 3. Different day
    it1 = MagicMock(item_type='milestone', label='2026-04-10', content='Duplicate Event')
    it2 = MagicMock(item_type='milestone', label='2026-04-10', content='Duplicate Event')
    it3 = MagicMock(item_type='milestone', label='2026-04-10', content='Unique Event')
    it4 = MagicMock(item_type='milestone', label='2026-03-20', content='Earlier Event')
    
    with patch("run.db.session_scope") as mock_scope:
        mock_sess = MagicMock()
        mock_scope.return_value.__enter__.return_value = mock_sess
        
        mock_sess.query.return_value.filter_by.return_value.all.return_value = [it1, it2, it3, it4]
        mock_sess.query.return_value.all.return_value = [mock_catalyst]
        # Skip other table queries
        mock_sess.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        data = load_db_data()
        timeline = data['catalysts']['catalysts'][0]['Timeline']
        
        # Expected sorting: March then April
        assert len(timeline) == 2
        
        # March entry
        assert timeline[0]['Time'] == '2026-03-20'
        assert timeline[0]['Event'] == 'Earlier Event'
        
        # April entry (merged and deduplicated)
        assert timeline[1]['Time'] == '2026-04-10'
        # 'Duplicate Event' + 'Unique Event'
        assert timeline[1]['Event'] == 'Duplicate Event; Unique Event'
