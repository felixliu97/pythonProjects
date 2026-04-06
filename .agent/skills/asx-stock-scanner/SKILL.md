---
name: asx-stock-scanner
description: Specialized skill for scanning and analyzing stocks on the Australian Securities Exchange (ASX).
---

# ASX Stock Scanner Skill

Use this skill for projects focusing on the Australian market (ASX).

## Market Reference

- **Timezone**: Australia/Sydney (AEST/AEDT).
- **Trading Hours**:
  - **Normal Trading**: 10:00 AM - 4:00 PM
  - Closing Auction: 4:00 PM - 4:10 PM
- **Currency**: AUD
- **Tickers**: Use `.AX` suffix (e.g., `BHP.AX`).

## Technical Strategy Reference

### Upside Potential Indicators
- **RSI Divergence**: Price lower lows + RSI higher lows = momentum shift.
- **Volume Breakout**: `Volume > 2 * SMA(Volume, 20)` + Price UP > 2%.
- **Golden Cross**: `SMA(50)` crossing above `SMA(200)`.

## Implementation Patterns

When scanning, always apply a **Liquidity Filter**:
- Minimum daily turnover: $100k AUD.
- Filter out "illiquid" or "zombie" stocks with zero volume days.

```python
import yfinance as yf

def fetch_asx(ticker):
    return yf.download(f"{ticker}.AX", period="1y")
```
