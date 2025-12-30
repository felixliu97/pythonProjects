# ASX Analyzer Requirements

## Overview
The **ASX Analyzer** is a Python-based utility designed to identify trending stocks and ETFs on the Australian Securities Exchange (ASX). It scores instruments based on price momentum, volume analysis, and technical indicators (RSI, Volatility) to help identify potential trading opportunities.

## System Requirements
*   **Python Version**: Python 3.7 or higher.
*   **Operating System**: Cross-platform (Windows, macOS, Linux).
*   **Network**: Active internet connection required to fetch real-time data from Yahoo Finance.

## Python Dependencies
The following external libraries are required:

| Library | Purpose |
| :--- | :--- |
| `yfinance` | Fetching historical market data and asset metadata. |
| `pandas` | Data manipulation, dataframe operations, and statistical calculations. |
| `numpy` | Numerical computing support for pandas. |

### Installation
You can install the dependencies via pip:
```bash
pip install yfinance pandas numpy
```

## Configuration
The application relies on a `config.json` file located in the script's directory.

**Required JSON Structure:**
*   `stocks`: Array of stock ticker strings (e.g., `"BHP.AX"`).
*   `etfs`: Array of ETF ticker strings (e.g., `"VAS.AX"`).
*   `weights`: (Optional) Scoring weights for different metrics (price_1d, volume_change, momentum, etc.).
*   `settings`: (Optional) Analysis parameters (e.g., `rsi_period`, `min_data_points`).
*   `thresholds`: (Optional) Alert triggers (e.g., `rsi_upper`, `price_change_alert`).

## Functional Requirements

### 1. Data Processing
*   **Concurrent Fetching**: Uses multi-threading (default 10 workers) to fetch data for multiple tickers simultaneously.
*   **Resilience**: Gracefully handles API errors or missing data for individual tickers without crashing the batch.
*   **ETF Filtering**: Automatically excludes ETFs with Total Assets (AUM) under $1 Billion.

### 2. Scoring Algorithm
The script assigns a "Trending Score" to each asset based on a weighted sum of:
*   **Price Momentum**: 1-day, 5-day, and 20-day percentage changes.
*   **Volume Analysis**: Current volume vs. historical average.
*   **Technical Signals**: Relative Strength Index (RSI) and Volatility (Std Dev of returns).

### 3. Output & Reporting
**Console Interface:**
*   Displays progress of data fetching.
*   Prints color-coded ASCII tables for Stocks and ETFs sorted by trending score.
*   Highlights significant metrics (green for positive, red for negative).

**HTML Report Generation:**
*   Generates a standalone file named `asx_report_YYYY-MM-DD.html`.
*   **Features**:
    *   Interactive tabs for Stocks and ETFs.
    *   Sortable columns (click headers).
    *   **Insights Section**:
        *   Top 3 Gainers & Decliners.
        *   Sector/Category performance averages.
        *   Volume Spike alerts (>30% vs avg).
        *   RSI Alerts (Overbought > 70, Oversold < 30).
