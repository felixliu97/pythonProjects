import pytest
import requests
from scripts.asx_analyzer import MomentumAnalyzer
from scripts.asx_catalysts import export_catalysts

@pytest.fixture
def analyzer():
    return MomentumAnalyzer(requests.Session())

# --- 1. Analyzer Logic ---

def test_calculate_momentum_score(analyzer):
    """Verify the scoring logic for stock momentum."""
    # Positive signals
    m_up = {
        'rsi': 25,          # Oversold bump (+10)
        'momentum': 2.0,    # Strong (+10)
        'price_diff_1d': 2.0, 
        'price_diff_5d': 5.0,
        'vol_change': 60
    }
    score_up = analyzer.calculate_score(m_up)
    assert score_up > 70
    
    # Negative signals
    m_down = {
        'rsi': 75,          # Overbought (-5)
        'momentum': -1.0,   # Weak (-5)
        'price_diff_1d': -2.0, 
        'price_diff_5d': -5.0,
        'vol_change': -20
    }
    score_down = analyzer.calculate_score(m_down)
    assert score_down < 50

def test_analyzer_field_presence(analyzer):
    """Verify that MomentumAnalyzer has required extraction methods."""
    assert hasattr(analyzer, 'fetch_fundamentals')
    assert hasattr(analyzer, 'analyze_ticker')

# --- 2. Catalyst Management ---

def test_catalyst_export_function():
    """Verify that asx_catalysts has the core export function."""
    assert callable(export_catalysts)
