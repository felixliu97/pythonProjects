import pytest
import requests
import pandas as pd
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

def test_calculate_rsi(analyzer):
    """Test RSI calculation with Wilder's smoothing."""
    # Standard 14-day sequence: 14 ups, then constant
    prices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
    series = pd.Series(prices)
    rsi = analyzer.calculate_rsi(series, period=14)
    # Should be 100 or very close to it as there are no down days
    assert rsi > 99
    
    # Sequence with a sharp drop
    prices_drop = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 10]
    series_drop = pd.Series(prices_drop)
    rsi_drop = analyzer.calculate_rsi(series_drop, period=14)
    # Should be much lower after a massive drop
    assert rsi_drop < 50

def test_analyze_ticker_prefers_live_daily_change_fields(analyzer, monkeypatch):
    """If ASX returns explicit daily change fields, they should override a misleading yfinance-derived 1D move."""
    hist = pd.DataFrame(
        {
            "Close": [0.0125] * 20,
            "Volume": [0] * 20,
        },
        index=pd.date_range("2026-04-01", periods=20, freq="B"),
    )

    analyzer.fetch_fundamentals = lambda symbol: {
        "marketCap": -1,
        "pe": -99999.99,
        "yield_val": 0,
        "industryGroup": "Materials",
        "displayName": "WA KAOLIN LIMITED",
        "priceLast": 0.025,
        "priceChange": 0,
        "priceChangePercent": 0,
    }

    class MockTicker:
        def history(self, period):
            return hist

    monkeypatch.setattr("scripts.asx_analyzer.yf.Ticker", lambda symbol: MockTicker())

    result = analyzer.analyze_ticker("WAK", "announcement")

    assert result is not None
    trend, meta = result
    assert meta == ("Materials", "WA KAOLIN LIMITED")
    assert trend.current_price == 0.025
    assert trend.price_change_1d == 0
    assert trend.price_diff_1d == 0
