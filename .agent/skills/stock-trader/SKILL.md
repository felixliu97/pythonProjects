---
name: stock-trader
description: Provides guidelines, templates, and best practices for building stock trading applications in Python. Use when working on trading bots or financial analysis tools.
---

# Stock Trader Skill

Use this skill when developing stock trading algorithms, backtesting engines, or financial data analysis tools.

## Project Structure

Recommended structure for a trading bot:

```
trading_bot/
├── data/               # Local data storage (csv, sqlite)
├── strategies/         # Trading strategies
│   ├── __init__.py
│   ├── base_strategy.py
│   └── mean_reversion.py
├── core/               # Core execution engine
│   ├── brokerage.py    # API wrappers (Alpaca, IBKR)
│   └── backtester.py   # Backtesting logic
├── config.py           # Configuration (API keys - load from env!)
├── requirements.txt
└── main.py             # Entry point
```

## Key Libraries

- **Data Analysis**: `pandas`, `numpy`
- **Technical Indicators**: `ta-lib`, `pandas-ta`
- **Brokerage APIs**: `alpaca-trade-api`, `ib_insync`, `ccxt` (crypto)
- **Backtesting**: `backtrader`, `zipline-reloaded`, `vectorbt`

## Data Handling Best Practices

- Always use **OHLCV** format (Open, High, Low, Close, Volume) for candle data.
- Ensure timezones are handled correctly (promote usage of UTC).
- Store historical data efficiently (Parquet or localized SQL database preferred over CSV for large datasets).

## Strategy Template

```python
class BaseStrategy:
    def __init__(self, symbol):
        self.symbol = symbol
        self.position = 0

    def on_market_data(self, data_point):
        """Called on every new price candle/tick"""
        raise NotImplementedError

    def generate_signal(self, df):
        """Analyze dataframe to produce buy/sell signal"""
        pass
```

## Risk Management

- **Never** hardcode API keys. Use `.env` files and `python-dotenv`.
- Implement a **Stop Loss** and **Take Profit** for every trade.
- Use **Position Sizing** rules (e.g., never risk more than 1-2% of portfolio per trade).
