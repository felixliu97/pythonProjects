# ASX Trend Analyzer

A Python-based utility that identifies trending stocks and ETFs on the Australian Securities Exchange (ASX). It scores instruments based on price momentum, volume analysis, and technical indicators (RSI, Volatility) to help identify potential trading opportunities.

## Quick Start

```bash
pip install yfinance pandas numpy pyyaml

python run.py analyzer
```

## Configuration

The application reads `config/asx_analyzer.yaml` for stock/ETF watchlists and scoring parameters.

**YAML Structure:**
- `stocks`: Array of stock ticker strings (e.g., `"BHP.AX"`)
- `etfs`: Array of ETF ticker strings (e.g., `"VAS.AX"`)
- `weights`: (Optional) Scoring weights for different metrics
- `settings`: (Optional) Analysis parameters (e.g., `rsi_period`, `min_data_points`)
- `thresholds`: (Optional) Alert triggers (e.g., `rsi_upper`, `price_change_alert`)

## System Requirements

- **Python**: 3.7+
- **Dependencies**: `yfinance`, `pandas`, `numpy`, `pyyaml`
- **Network**: Active internet connection required (Yahoo Finance API)

## Scoring Algorithm

Assigns a "Trending Score" to each asset based on a weighted sum of:
- **Price Momentum**: 1-day, 5-day, and 20-day percentage changes
- **Volume Analysis**: Current volume vs. historical average
- **Technical Signals**: RSI and Volatility (Std Dev of returns)

## Output

- **Console**: Color-coded ASCII tables sorted by trending score
- **HTML**: `output/asx_analyzer.html` — Interactive dashboard with sortable columns, insights section (top gainers/decliners, sector performance, volume spikes, RSI alerts)

## Data Processing

- **Concurrent Fetching**: 10 worker threads for simultaneous data retrieval
- **Resilience**: Gracefully handles API errors for individual tickers
- **ETF Filtering**: Excludes ETFs with AUM under $1 Billion
