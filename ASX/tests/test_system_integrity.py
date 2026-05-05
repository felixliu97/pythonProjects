import re
from pathlib import Path

import pytest


class TestSystemIntegrity:
    """
    Ensures that Documentation (README) and UI (Dashboard)
    stay in sync to prevent regression bugs.
    """

    def get_readme_content(self):
        readme_path = Path(__file__).parent.parent / "README.md"
        return readme_path.read_text(encoding="utf-8")

    def get_html_template_content(self):
        template_path = Path(__file__).parent.parent / "templates" / "asx_dashboard.html"
        return template_path.read_text(encoding="utf-8")

    def test_readme_mentions_all_indicators(self):
        """Check if README.md is updated when new technical indicators are added."""
        readme = self.get_readme_content()
        # Indicators we expect to be documented
        indicators = ["RSI", "Wilder", "Score", "Momentum", "Volatility", "Volume"]

        for ind in indicators:
            assert ind.lower() in readme.lower(), (
                f"Indicator '{ind}' is NOT documented in README.md! Please update documentation."
            )

    def test_ui_model_sync(self):
        """Verify that fields calculated in analyzer are actually referenced in the HTML template."""
        html = self.get_html_template_content()

        # If these are in the model, they should probably be in the UI
        ui_keywords = {
            "rsi": ["RSI", "rsi"],
            "score": ["Score", "score"],
            "volume": ["Vol Surge", "volume_change"],
            "market_cap": ["Cap", "marketCap"],
        }

        for logic_name, ui_patterns in ui_keywords.items():
            found = any(pattern in html for pattern in ui_patterns)
            assert found, f"Field logic '{logic_name}' exists but no reference found in asx_dashboard.html"

    def test_announcement_rating_logic_sync(self):
        """Verify that the rating rules in README match the actual code keywords."""
        readme = self.get_readme_content()

        # Check if 'Strong Phrases' in README mention at least one key phrase from script
        if "Strong Phrases" in readme:
            # Look for common high-value phrases in script
            high_value_keywords = ["high-grade", "discovery", "binding", "dfs"]
            found_in_readme = any(kw.lower() in readme.lower() for kw in high_value_keywords)
            assert found_in_readme, "Announcement rating keywords in script changed but README not updated."

    def test_version_consistency(self):
        """Ensure README.md and HTML Dashboard share the same version number (vX.X)."""
        readme = self.get_readme_content()
        html = self.get_html_template_content()

        # 1. Extract from README (first occurrence of vX.X)
        readme_match = re.search(r"v\d+\.\d+", readme)
        assert readme_match, "No version (vX.X) found in README.md header"
        readme_ver = readme_match.group(0)

        # 2. Extract from HTML Title
        title_match = re.search(r"<title>.*?v(\d+\.\d+)</title>", html)
        assert title_match, "No version found in HTML <title>"
        html_title_ver = "v" + title_match.group(1)

        # 3. Extract from HTML Header Pill
        header_match = re.search(r"v(\d+\.\d+)</span>\s*</h1>", html)
        assert header_match, "No version badge found in HTML header"
        html_header_ver = "v" + header_match.group(1)

        assert readme_ver == html_title_ver, f"Version mismatch: README({readme_ver}) vs HTML Title({html_title_ver})"
        assert readme_ver == html_header_ver, (
            f"Version mismatch: README({readme_ver}) vs HTML Header({html_header_ver})"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
