import pytest
import requests
from scripts.asx_analyzer import MomentumAnalyzer

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

def test_score_clamped_to_boundaries(analyzer):
    """Score must always be in [0, 100] even with extreme inputs."""
    # Extremely bullish signals should cap at 100
    m_extreme_up = {
        'rsi': 10, 'momentum': 10.0,
        'price_diff_1d': 50.0, 'price_diff_5d': 100.0,
        'vol_change': 500
    }
    assert 0 <= analyzer.calculate_score(m_extreme_up) <= 100
    
    # Extremely bearish signals should floor at 0
    m_extreme_down = {
        'rsi': 95, 'momentum': -10.0,
        'price_diff_1d': -50.0, 'price_diff_5d': -100.0,
        'vol_change': -90
    }
    assert 0 <= analyzer.calculate_score(m_extreme_down) <= 100
