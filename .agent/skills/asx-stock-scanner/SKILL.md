---
name: asx-stock-scanner
description: Specialized skill for scanning and analyzing stocks on the Australian Securities Exchange (ASX).
---

# ASX Stock Scanner Skill

Use this skill for projects focusing on the Australian market (ASX).

## Data Sources

- **Yahoo Finance**: Use the `.AX` suffix for ASX symbols (e.g., `BHP.AX`, `CBA.AX`).
  - Library: `yfinance`
- **ASX Website**: Defines official listings and upcoming dividends.
- **IRESS**: For professional, paid data feeds.

## Market Details

- **Timezone**: Australia/Sydney (AEST/AEDT).
- **Market Hours**:
  - Pre-open: 7:00 AM - 10:00 AM
  - **Normal Trading**: 10:00 AM - 4:00 PM
  - Closing Auction: 4:00 PM - 4:10 PM
- **Currency**: AUD

## Obtaining ASX Listings

To scan the market, you first need a list of tickers.
1. Download the official list from the [ASX Website](https://www.asx.com.au/).
2. Or use a library to fetch indices (e.g., ASX 200 components).

## Scanning & Filtering Patterns

When scanning thousands of stocks, filter efficiently:

1. **Liquidity Filter**: Remove stocks with low average volume (e.g., < $100k daily turnover).
2. **Penny Stocks**: Be careful with stocks < $0.10; they often have different tick sizes.
3. **Sector Rotation**: The ASX is heavy on Financials and Materials (Miners). Pay attention to commodity prices.

## Scanning for Upside Potential

Strategies to identify stocks with short or mid-term growth potential:

### Short-Term Upside (Swing Trading)
- **RSI Divergence**: Look for stocks where price is making lower lows but RSI (14) is making higher lows. This indicates momentum is shifting.
- **Volume Breakout**: Watch for `Volume > 2 * AverageVolume(20)` combined with a price increase > 2%.
- **MACD Bullish Crossover**: MACD line crossing ABOVE the Signal line, ideally while below the zero line.

### Mid-Term Upside (Trend Following)
- **Golden Cross**: The 50-day SMA crossing above the 200-day SMA. A classic long-term buy signal.
- **Trend Alignment**: Filter for `Close > SMA(50)` AND `SMA(50) > SMA(200)`.
- **Consolidation Breakout**: Identify stocks trading in a tight range (e.g., Bollinger Band width narrowing) that suddenly break out above the upper band.

## Example: Fetching ASX Data

```python
import yfinance as yf

def get_asx_data(ticker):
    if not ticker.endswith('.AX'):
        ticker += '.AX'
    return yf.download(ticker, period="1y")

# Example: Get BHP data
bhp = get_asx_data("BHP")
```
