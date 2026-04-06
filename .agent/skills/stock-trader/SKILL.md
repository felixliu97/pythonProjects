---
name: stock-trader
description: Technical guidelines, standards, and libraries for building trading applications in Python.
---

# Stock Trader Skill (Technical)

Technical reference and mandatory standards for financial engineering.

## Key Libraries
- **Data Analysis**: `pandas`, `numpy`, `scipy`.
- **Technical Indicators**: `pandas-ta`, `ta-lib`.
- **Execution/APIs**: `alpaca-trade-api`, `ccxt`, `ib_insync`, `yfinance`.

## Data Handling Standards
- **Format**: Always use **OHLCV** (Open, High, Low, Close, Volume).
- **Storage**: Prefer **Parquet** or **SQL** (PostgreSQL/SQLite) for performance; avoid large CSVs.
- **Timezones**: Force **UTC** for all internal processing. Use `pytz` or `zoneinfo`.
- **Reproducibility**: Ensure backtests are deterministic (use fixed seeds for any random components).

## Risk & Safety (Mandatory)
- **Environment**: No hardcoded API keys. Use `.env`.
- **Order Protection**: Every order must have an associated **Stop Loss** and **Take Profit**.
- **Position Sizing**: Limit per-trade risk to 1-2% of total equity.
- **Safety**: Implement a **"Kill Switch"** (emergency flatten all positions) for any live execution logic.
