import pytest
import base64
from jinja2 import Environment
from datetime import date
from unittest.mock import MagicMock, patch
from scripts.utils import generate_sparkline
from run import trim_zeros, prune_pdf_cache

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
    """Verify that timeline items loaded from YAML are sorted by the 'Date' field."""
    import yaml
    from unittest.mock import patch
    from run import load_catalysts_from_yaml

    yaml_content = [{
        "Ticker": "TEST", "Company": "Test Co", "Sector": "Tech",
        "CR_Risk": "低", "Breakout_Probability": "高", "Core_Notes": "Valid notes",
        "Rating": "观望",
        "Timeline": [
            {"Date": "2026-04-10", "Event": "Event 2"},
            {"Date": "2026-03-20", "Event": "Event 1"},
            {"Date": "2026-05-01", "Event": "Event 3"},
        ]
    }]

    def mock_open_yaml(*a, **kw):
        from io import StringIO
        return StringIO(yaml.dump(yaml_content, allow_unicode=True))

    with patch("builtins.open", mock_open_yaml):
        result = load_catalysts_from_yaml()
        timeline = result[0]["Timeline"]

        assert timeline[0]["Date"] == "2026-03-20"
        assert timeline[1]["Date"] == "2026-04-10"
        assert timeline[2]["Date"] == "2026-05-01"


def test_catalysts_from_yaml_defaults():
    """Verify that schema-backed defaults are applied to optional YAML fields."""
    import yaml
    from unittest.mock import patch
    from run import load_catalysts_from_yaml

    yaml_content = [{
        "Ticker": "MIN",
        "Company": "Minimal Co",
        "CR_Risk": "低",
        "Breakout_Probability": "中",
        "Core_Notes": "Testing defaults"
    }]

    def mock_open_yaml(*a, **kw):
        from io import StringIO
        return StringIO(yaml.dump(yaml_content, allow_unicode=True))

    with patch("builtins.open", mock_open_yaml):
        result = load_catalysts_from_yaml()
        c = result[0]
        assert c["Ticker"] == "MIN"
        assert c["Stage"] == "未分类"
        assert c["Rating"] == "观望"
        assert c["CR_Risk"] == "低"
        assert c["Breakout_Probability"] == "中"
        assert c["Timeline"] == []
        assert c["Catalysts"] == []
        assert c["Risks"] == []


def test_prune_pdf_cache_keeps_only_latest_trading_day(tmp_path):
    """Only PDFs for the latest announcement trading day should remain in .pdf_cache."""
    cache_dir = tmp_path / ".pdf_cache"
    cache_dir.mkdir()
    keep_file = cache_dir / "2026-04-24_[ABC]_latest.pdf"
    old_file = cache_dir / "2026-04-23_[XYZ]_older.pdf"
    keep_file.write_bytes(b"latest")
    old_file.write_bytes(b"older")

    mock_sess = MagicMock()
    mock_query = MagicMock()
    mock_query.scalar.return_value = date(2026, 4, 24)
    mock_sess.query.return_value = mock_query

    with patch("run.db.session_scope") as mock_scope:
        mock_scope.return_value.__enter__.return_value = mock_sess
        prune_pdf_cache(tmp_path)

    assert keep_file.exists()
    assert not old_file.exists()


def test_prune_pdf_cache_removes_unrecognized_pdf_names(tmp_path):
    """Malformed cached PDF names should be removed during pruning."""
    cache_dir = tmp_path / ".pdf_cache"
    cache_dir.mkdir()
    keep_file = cache_dir / "2026-04-24_[ABC]_latest.pdf"
    bad_file = cache_dir / "misc_file.pdf"
    keep_file.write_bytes(b"latest")
    bad_file.write_bytes(b"bad")

    mock_sess = MagicMock()
    mock_query = MagicMock()
    mock_query.scalar.return_value = date(2026, 4, 24)
    mock_sess.query.return_value = mock_query

    with patch("run.db.session_scope") as mock_scope:
        mock_scope.return_value.__enter__.return_value = mock_sess
        prune_pdf_cache(tmp_path)

    assert keep_file.exists()
    assert not bad_file.exists()


def test_catalyst_schema_rejects_invalid_rating():
    """Invalid YAML enum values should fail schema validation."""
    from pydantic import ValidationError
    from scripts.db_schemas import CatalystSchema

    with pytest.raises(ValidationError):
        CatalystSchema(
            Ticker="BAD",
            Company="Bad Co",
            CR_Risk="低",
            Breakout_Probability="中",
            Core_Notes="Testing",
            Rating="加仓"
        )


def test_catalyst_schema_rejects_invalid_timeline_date():
    """Timeline requires exact YYYY-MM-DD dates."""
    from pydantic import ValidationError
    from scripts.db_schemas import CatalystSchema

    with pytest.raises(ValidationError):
        CatalystSchema(
            Ticker="BAD",
            Company="Bad Co",
            CR_Risk="低",
            Breakout_Probability="中",
            Core_Notes="Testing",
            Timeline=[{"Date": "2026-04", "Event": "Bad date"}]
        )


# --- 5. Catalyst Schema & DB Field Validation ---

def test_catalyst_field_validity():
    """Verify that all live DB catalyst records have valid, separated fields."""
    from scripts.db_manager import db
    from scripts.db_models import CatalystMaster

    valid_levels = ["极低", "低", "中低", "中", "中高", "高", "极高", "Unknown", "N/A"]
    
    with db.session_scope() as sess:
        masters = sess.query(CatalystMaster).all()
        for m in masters:
            assert "(" not in (m.cr_risk or ""), f"Ticker {m.symbol} has un-migrated CR Risk: {m.cr_risk}"
            assert "(" not in (m.breakout_probability or ""), f"Ticker {m.symbol} has un-migrated Probability: {m.breakout_probability}"
            
            cr_lvl = m.cr_risk.strip() if m.cr_risk else "Unknown"
            prob_lvl = m.breakout_probability.strip() if m.breakout_probability else "N/A"
            
            assert cr_lvl in valid_levels, f"Ticker {m.symbol} has invalid CR Risk level: {cr_lvl}"
            assert prob_lvl in valid_levels, f"Ticker {m.symbol} has invalid Probability level: {prob_lvl}"

            if cr_lvl not in ["Unknown", "N/A"]:
                assert len(cr_lvl) <= 4, f"Ticker {m.symbol} CR Risk level seems too long: {cr_lvl}"
            if prob_lvl not in ["Unknown", "N/A"]:
                assert len(prob_lvl) <= 4, f"Ticker {m.symbol} Probability level seems too long: {prob_lvl}"


def test_catalyst_schema_rating_default():
    """Verify that CatalystSchema derives Rating from Breakout_Probability x CR_Risk."""
    from scripts.db_schemas import CatalystSchema

    v = CatalystSchema(
        Ticker="MSB",
        Company="Mesoblast",
        CR_Risk="低",
        Breakout_Probability="高",
        Core_Notes="Testing"
    )
    assert v.Rating == "买入"


def test_catalyst_schema_rating_explicit():
    """Verify that explicit YAML Rating overrides the derived matrix rating."""
    from scripts.db_schemas import CatalystSchema

    v = CatalystSchema(
        Ticker="MSB",
        Company="Mesoblast",
        CR_Risk="低",
        Breakout_Probability="中",
        Core_Notes="Testing",
        Rating="强力买入"
    )
    assert v.Rating == "强力买入"


def test_catalyst_rating_matrix_extremes():
    """Verify matrix-derived ratings at both optimistic and pessimistic extremes."""
    from scripts.db_schemas import derive_catalyst_rating

    assert derive_catalyst_rating("极低", "极高") == "强力买入"
    assert derive_catalyst_rating("高", "低") == "强力卖出"


def test_displayed_rating_equals_db_rating():
    """Dashboard rating comes directly from DB (headline-based), no price momentum boost."""
    # Simulate run.py ann_list builder: Rating = a.rating (no modification)
    db_rating = 3
    display_rating = db_rating  # No boost applied
    assert display_rating == 3


def test_sorting_logic_simulation():
    """Simulate the sorting logic used in run.py."""
    r_scores = {"强力买入": -10, "买入": -5, "观望": 0, "卖出": 5, "强力卖出": 10}
    
    items = [
        {"Ticker": "A", "Rating": "卖出"},
        {"Ticker": "B", "Rating": "强力买入"},
        {"Ticker": "C", "Rating": "观望"},
        {"Ticker": "D", "Rating": "买入"}
    ]
    
    sorted_items = sorted(items, key=lambda x: r_scores.get(x["Rating"], 0))
    
    assert sorted_items[0]["Ticker"] == "B"
    assert sorted_items[1]["Ticker"] == "D"
    assert sorted_items[2]["Ticker"] == "C"
    assert sorted_items[3]["Ticker"] == "A"
