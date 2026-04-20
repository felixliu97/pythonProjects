"""
Unit tests for dashboard field name consistency across all tabs.
Ensures the same field has the same name in different tables.
"""

import pytest
from pathlib import Path
import re


class TestDashboardFieldConsistency:
    """Test suite for verifying field naming consistency in asx_dashboard.html"""

    @pytest.fixture
    def template_content(self):
        """Load the dashboard template content."""
        template_path = Path(__file__).parent.parent / "templates" / "asx_dashboard.html"
        if not template_path.exists():
            pytest.skip("Dashboard template not found")
        return template_path.read_text(encoding="utf-8")

    @pytest.fixture
    def table_headers(self, template_content):
        """Extract all table headers from the template."""
        # Pattern to find <th>...</th> content within <thead> sections
        thead_pattern = r'<thead>(.*?)</thead>'
        th_pattern = r'<th[^>]*>(.*?)</th>'

        tables = {}
        table_ids = [
            'growthStockTable',
            'foundationStockTable',
            'etfTable',
            'catalystTable',
            'annTable',
            'placTable'
        ]

        for table_id in table_ids:
            # Find table with this id
            table_pattern = rf'<table[^>]*id="{table_id}"[^>]*>(.*?)</table>'
            table_match = re.search(table_pattern, template_content, re.DOTALL)
            if table_match:
                thead_match = re.search(thead_pattern, table_match.group(1), re.DOTALL)
                if thead_match:
                    th_matches = re.findall(th_pattern, thead_match.group(1))
                    # Clean up HTML tags and normalize
                    headers = []
                    for th in th_matches:
                        # Remove HTML tags, normalize whitespace
                        clean = re.sub(r'<[^>]+>', '', th).strip()
                        clean = re.sub(r'\s+', ' ', clean)
                        if clean:
                            headers.append(clean)
                    tables[table_id] = headers

        # Catalyst table uses class="catalyst-table" (no id)
        if 'catalystTable' not in tables:
            catalyst_pattern = r'<table[^>]*class="[^"]*catalyst-table[^"]*"[^>]*>(.*?)</table>'
            catalyst_match = re.search(catalyst_pattern, template_content, re.DOTALL)
            if catalyst_match:
                thead_match = re.search(thead_pattern, catalyst_match.group(1), re.DOTALL)
                if thead_match:
                    th_matches = re.findall(th_pattern, thead_match.group(1))
                    headers = []
                    for th in th_matches:
                        clean = re.sub(r'<[^>]+>', '', th).strip()
                        clean = re.sub(r'\s+', ' ', clean)
                        if clean:
                            headers.append(clean)
                    tables['catalystTable'] = headers

        return tables

    def test_ticker_field_consistency(self, table_headers):
        """Test that the ticker/code field is consistently named 'Ticker' across tabs."""
        ticker_tabs = {
            'growthStockTable': 'Ticker',
            'foundationStockTable': 'Ticker',
            'etfTable': 'Ticker',
            'annTable': 'Ticker',  # Should be 'Ticker', not 'Code'
            'placTable': 'Ticker',  # Should be 'Ticker', not 'Code'
        }

        for table_id, expected in ticker_tabs.items():
            if table_id in table_headers:
                headers = table_headers[table_id]
                assert expected in headers, \
                    f"{table_id}: Expected '{expected}' in headers, got {headers}"

    def test_company_field_consistency(self, table_headers):
        """Test that the company name field is consistently named 'Company' across tabs."""
        company_tabs = {
            'growthStockTable': 'Name',  # Special case: uses 'Name' not 'Company'
            'foundationStockTable': 'Name',
            'etfTable': 'Fund Name',  # Special case: ETFs use 'Fund Name'
            'annTable': 'Company',
            'placTable': 'Company',
        }

        for table_id, expected in company_tabs.items():
            if table_id in table_headers:
                headers = table_headers[table_id]
                # For ETFs, check that it contains 'Name'
                if expected == 'Fund Name':
                    assert any('Name' in h for h in headers), \
                        f"{table_id}: Expected header containing 'Name', got {headers}"
                else:
                    assert expected in headers, \
                        f"{table_id}: Expected '{expected}' in headers, got {headers}"

    def test_date_field_consistency(self, table_headers):
        """Test that date fields are consistently named."""
        date_tabs = ['annTable', 'placTable']
        for table_id in date_tabs:
            if table_id in table_headers:
                assert 'Date' in table_headers[table_id], \
                    f"{table_id}: Expected 'Date' in headers"

    def test_price_field_consistency(self, table_headers):
        """Test that price fields are consistently named."""
        price_tabs = {
            'growthStockTable': 'Price',
            'foundationStockTable': 'Price',
            'etfTable': 'Price',
            'annTable': 'Price',
            'placTable': 'Price',  # Should be 'Price', not 'Live'
        }

        for table_id, expected in price_tabs.items():
            if table_id in table_headers:
                headers = table_headers[table_id]
                assert expected in headers, \
                    f"{table_id}: Expected '{expected}' in headers, got {headers}"

    def test_pdf_field_consistency(self, table_headers):
        """Test that PDF/link fields are consistently named 'PDF'."""
        pdf_tabs = ['annTable', 'placTable']
        for table_id in pdf_tabs:
            if table_id in table_headers:
                headers = table_headers[table_id]
                assert 'PDF' in headers, \
                    f"{table_id}: Expected 'PDF' in headers, got {headers}"

    def test_one_d_percent_consistency(self, table_headers):
        """Test that 1D % field exists in relevant tables."""
        one_d_tabs = ['growthStockTable', 'foundationStockTable', 'etfTable', 'annTable']
        for table_id in one_d_tabs:
            if table_id in table_headers:
                headers = table_headers[table_id]
                assert '1D %' in headers, \
                    f"{table_id}: Expected '1D %' in headers, got {headers}"

    def test_five_d_percent_consistency(self, table_headers):
        """Test that 5D % field exists in relevant tables."""
        five_d_tabs = ['growthStockTable', 'foundationStockTable', 'etfTable']
        for table_id in five_d_tabs:
            if table_id in table_headers:
                headers = table_headers[table_id]
                assert '5D %' in headers, \
                    f"{table_id}: Expected '5D %' in headers, got {headers}"

    def test_catalyst_table_has_required_fields(self, table_headers):
        """Test that catalyst table has all required fields."""
        if 'catalystTable' not in table_headers:
            pytest.skip("catalystTable not found in template")

        headers = table_headers['catalystTable']
        required_fields = ['Stage', 'Ticker Name', 'Rating', 'CR Risk']

        for field in required_fields:
            assert field in headers, \
                f"catalystTable: Expected '{field}' in headers, got {headers}"

    def test_catalyst_rating_uses_hidden_sort_key(self, template_content):
        """Catalyst Rating column should include a hidden numeric sort key for stable table sorting."""
        assert '{% set r_sort =' in template_content
        assert '<span style="display:none">{{ r_sort }}</span>' in template_content

    def test_indicator_field_consistency(self, table_headers):
        """Test that technical indicators (Score, RSI, Vol Surge) exist in relevant tables."""
        indicator_tabs = {
            'growthStockTable': ['Score', 'RSI', 'Vol Surge'],
            'foundationStockTable': ['Score', 'RSI', 'Vol Surge'],
            'etfTable': ['Score', 'RSI', 'Vol Surge'],
            'annTable': ['RSI'],
        }

        for table_id, expected_fields in indicator_tabs.items():
            if table_id in table_headers:
                headers = table_headers[table_id]
                for field in expected_fields:
                    assert field in headers, \
                        f"{table_id}: Expected indicator '{field}' in headers, got {headers}"

    def test_fundamental_field_consistency(self, table_headers):
        """Test that fundamental fields (Cap/Assets, P/E/Yield, Industry) exist in relevant tables."""
        fundamental_tabs = {
            'growthStockTable': ['Cap', 'P/E', 'Industry'],
            'foundationStockTable': ['Cap', 'P/E', 'Industry'],
        }

        for table_id, expected_fields in fundamental_tabs.items():
            if table_id in table_headers:
                headers = table_headers[table_id]
                for field in expected_fields:
                    assert field in headers, \
                        f"{table_id}: Expected fundamental '{field}' in headers, got {headers}"
        
        # Special check for ETF table
        if 'etfTable' in table_headers:
            headers = table_headers['etfTable']
            assert 'Total Assets' in headers, f"etfTable: Expected 'Total Assets' in headers, got {headers}"
            assert 'Yield' in headers, f"etfTable: Expected 'Yield' in headers, got {headers}"
            assert 'Fund Name' in headers, f"etfTable: Expected 'Fund Name' in headers, got {headers}"

    def test_placement_specific_fields(self, table_headers):
        """Test that placement-specific fields exist in the placement table."""
        if 'placTable' in table_headers:
            headers = table_headers['placTable']
            expected = ['CR Price', 'Diff %', 'Placement Event Detail']
            for field in expected:
                assert field in headers, \
                    f"placTable: Expected '{field}' in headers, got {headers}"

    def test_announcement_specific_fields(self, table_headers):
        """Test that announcement-specific fields exist in the news feed table."""
        if 'annTable' in table_headers:
            headers = table_headers['annTable']
            assert 'Headline & Summary' in headers, \
                f"annTable: Expected 'Headline & Summary' in headers, got {headers}"

    def test_no_duplicate_field_names(self, table_headers):
        """Test that no table has duplicate field names."""
        for table_id, headers in table_headers.items():
            duplicates = [h for h in set(headers) if headers.count(h) > 1]
            assert not duplicates, \
                f"{table_id}: Duplicate field names found: {duplicates}"

    def test_standardized_field_reference(self, table_headers):
        """Documentation test: verify standardized field names are documented."""
        # This test serves as documentation of the standard field names
        standard_fields = {
            'Ticker': ['growthStockTable', 'foundationStockTable', 'etfTable', 'annTable', 'placTable'],
            'Date': ['annTable', 'placTable'],
            'Price': ['growthStockTable', 'foundationStockTable', 'etfTable', 'annTable', 'placTable'],
            '1D %': ['growthStockTable', 'foundationStockTable', 'etfTable', 'annTable'],
            'Rating': ['annTable', 'catalystTable'],
            'PDF': ['annTable', 'placTable'],
            'RSI': ['growthStockTable', 'foundationStockTable', 'etfTable', 'annTable'],
            'Score': ['growthStockTable', 'foundationStockTable', 'etfTable'],
        }

        for field, expected_tabs in standard_fields.items():
            for table_id in expected_tabs:
                if table_id in table_headers:
                    assert field in table_headers[table_id], \
                        f"Standard field '{field}' missing from {table_id}"


class TestDataFieldMapping:
    """Test suite for verifying data field mappings in run.py"""

    @pytest.fixture
    def run_py_content(self):
        """Load the run.py content."""
        run_path = Path(__file__).parent.parent / "run.py"
        if not run_path.exists():
            pytest.skip("run.py not found")
        return run_path.read_text(encoding="utf-8")

    def test_announcement_data_fields(self, run_py_content):
        """Test that announcement data structure has consistent field names."""
        # Check for Price_Diff_1d field
        assert 'Price_Diff_1d' in run_py_content, \
            "Announcement data should include 'Price_Diff_1d' field"
        assert 'Current_Price' in run_py_content, \
            "Announcement data should include 'Current_Price' field"

    def test_placement_data_fields(self, run_py_content):
        """Test that placement data structure has consistent field names."""
        # Check for consistent naming
        assert 'Price_Diff_%' in run_py_content or "'Price_Diff_%'" in run_py_content, \
            "Placement data should include 'Price_Diff_%' field"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
