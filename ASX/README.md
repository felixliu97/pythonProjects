# ASX Market Analysis & Research Suite

A comprehensive, unified Python suite for Australian Securities Exchange (ASX) data extraction, market analysis, and fundamental catalyst tracking. 

## Project Architecture

The suite follows a **Headless Data Engine** pattern: individual modules extract and process raw data into JSON/YAML, while a single Unified Dashboard serves as the presentation layer.

```text
ASX/
│
├── asx_analyzer/         # Momentum, volume, and RSI screener for Stocks/ETFs
├── asx_announcements/    # price-sensitive market announcement tracker
├── asx_catalysts/        # Fundamental catalyst radar & database
├── asx_placements/       # Capital raising discovery & PDF extractor
│
├── config/               # Source metadata and database storage
│   ├── asx_analyzer.yaml       # Analyzer watchlists (Growth/Foundation)
│   ├── asx_announcements.yaml  # Persistent history of news items
│   ├── asx_catalysts.yaml      # Master catalyst database
│   └── asx_placements.yaml     # Capital raising history
│
├── templates/            # Global UI Templates
│   ├── asx_dashboard.html      # Unified Pro Dashboard (Jinja2)
│   └── base.css                # Shared modern styling
│
├── output/               # Production Data & UI
│   ├── asx_dashboard.html      # THE UNIFIED HUB (Open this for results)
│   ├── asx_analyzer.json       # Ingested by dashboard
│   ├── asx_announcements.json  # Ingested by dashboard
│   ├── asx_catalysts.json      # Ingested by dashboard
│   └── asx_placements.json     # Ingested by dashboard
│
└── run.py                # Unified CLI runner (Entry point)
```

## Modules

### 1. Catalyst Radar (`asx_catalysts`)
Compiles tracking information of high-conviction fundamental plays.
- **Risk-Adjusted Sorting**: Rankings based on Probability (High->Low) and CR Risk (Low->High).
- **Headless Mode**: Exports structured research to JSON for the master dashboard.

### 2. Market Analyzer (`asx_analyzer`)
Pulls live market data for predefined set of tickers.
- **Categorized View**: Specialized tracking for **Growth / Catalyst** and **Large Cap / Foundation** stocks.
- **Momentum Scoring**: Proprietary 100-point score using price action (1D/5D/20D), Volume Breaks, and RSI.

### 3. Announcements Scanner (`asx_announcements`)
Directly polls the ASX MarkIt API for news.
- **AI-Ready Summary**: Uses `pdfplumber` to extract text and builds structured news datasets.
- **Rolling Retention**: Maintains a high-signal 7-day rolling window of price-sensitive news.

### 4. Placements Scanner (`asx_placements`)
Targeted pipeline for capital raisings.
- **Discount Detection**: Extracts issuance prices out of PDFs and compares them to real-time market prices.

## Unified CLI

Every data command now **automatically synchronizes** with the dashboard.

```bash
python run.py catalysts          # Sync Catalysts -> Dashboard
python run.py analyzer           # Sync Market Trends -> Dashboard
python run.py announcements      # Sync News Feed -> Dashboard
python run.py placements         # Sync Placements -> Dashboard
python run.py dashboard          # Regenerate dashboard from existing data
python run.py all                # Full pipeline run (Refresh everything)
```

## Data Pipeline

```
[ ASX API / yFinance ] 
         ↓
  [ Data Engines ] (Python + PDF Extractors)
         ↓
 [ Structured JSON ] (output/*.json)
         ↓
[ Unified Dashboard ] (Jinja2 + asx_dashboard.html)
```

> [!TIP]
> Always use **run.py** as your entry point. The individual module scripts are "headless" and no longer generate standalone HTML files.
