"""
Unit tests for dashboard template rendering.
Ensures that the dashboard builds successfully even when data contains None values for fields that might fail formatting (like prices or RSI).
"""

import pytest
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# Need to import the trim_zeros filter from run.py
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))
from run import trim_zeros

class TestDashboardRendering:
    @pytest.fixture
    def template(self):
        """Load the dashboard template with the appropriate environment."""
        template_dir = Path(__file__).parent.parent / "templates"
        if not template_dir.exists():
            pytest.skip("Templates directory not found")
        
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        env.filters["trim_zeros"] = trim_zeros
        return env.get_template("asx_dashboard.html")

    def test_render_with_none_values(self, template):
        """Test that the template can render successfully when numeric fields are None."""
        
        # This matches the EXACT logic of run.py's load_db_data
        # t.score or 0.0 means it will be 0.0, NOT None.
        # But trend.rsi if trend else None means it CAN be None.
        mock_data = {
            "analyzer": {
                "growth_stocks": [{
                    "symbol": "WAU",
                    "name": "WAU Corp",
                    "industry": "Mining",
                    "current_price": 0.0,
                    "marketCap": 0,
                    "pe": None,
                    "yield": 0.0,
                    "score": 0.0,
                    "price_change_1d": 0.0,
                    "price_diff_1d": 0.0,
                    "price_change_5d": 0.0,
                    "price_diff_5d": 0.0,
                    "momentum": 0.0,
                    "volatility": 0.0,
                    "volume_change": 0.0,
                    "rsi": 0.0,
                    "sparkline": "dummy.png"
                }],
                "foundation_stocks": [],
                "etfs": [{
                    "symbol": "ETF",
                    "name": "ETF Fund",
                    "marketCap": 0,
                    "current_price": 0.0,
                    "yield": 0.0,
                    "score": 0.0,
                    "price_change_1d": 0.0,
                    "price_diff_1d": 0.0,
                    "price_change_5d": 0.0,
                    "price_diff_5d": 0.0,
                    "momentum": 0.0,
                    "volatility": 0.0,
                    "volume_change": 0.0,
                    "rsi": 0.0,
                    "sparkline": "dummy.png"
                }],
                "global_timeline": []
            },
            "catalysts": {
                "catalysts": [{
                    "Ticker": "WAU",
                    "Stage": "阶段1-无人关注期",
                    "Sector": "Mining",
                    "Timeline": [],
                    "Catalysts": [],
                    "Risks": [],
                    "Rating": "观望",
                    "CR_Risk": "高",
                    "Breakout_Probability": "中",
                    "Core_Notes": ""
                }]
            },
            "announcements": {
                "announcements": [{
                    "Date": "2026-04-22",
                    "ASX_Code": "WAU",
                    "Company": "WAU Corp",
                    "Headline": "Test Announcement",
                    "Summary": "Summary",
                    "Current_Price": None,
                    "Price_Change_1d": 0.0,
                    "Price_Diff_1d": 0.0,
                    "Rating": 0,
                    "RSI": None,
                    "PDF_Link": "#"
                }]
            },
            "placements": {
                "placements": [{
                    "Date": "2026-04-22",
                    "ASX_Code": "WAU",
                    "Company": "WAU Corp",
                    "Headline": "Test Placement",
                    "CR_Price": None,
                    "Current_Price": None,
                    "Price_Diff_%": 0.0,
                    "PDF_Link": "#"
                }]
            },
            "timestamp": "2026-04-22 10:00:00"
        }

        try:
            rendered_html = template.render(**mock_data)
        except TypeError as e:
            pytest.fail(f"Template rendering failed with TypeError: {e}")
        except Exception as e:
            pytest.fail(f"Template rendering failed with Exception: {e}")

        assert "WAU Corp" in rendered_html
        assert "Test Announcement" in rendered_html
