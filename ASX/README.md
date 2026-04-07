# ASX Market Analysis & Research Suite

A comprehensive, unified Python suite for Australian Securities Exchange (ASX) data extraction, market analysis, and fundamental catalyst tracking. 

## Project Architecture

```
ASX/
│
├── asx_analyzer/         # Technical momentum, volume, and RSI screener for Stocks/ETFs
├── asx_announcements/    # Automated tracker for price-sensitive market announcements
├── asx_catalysts/        # Fundamental tracked catalyst radar builder (HTML)
├── asx_placements/       # Capital raising and placement discount detection tool
│
├── .pdf_cache/           # Shared fast-access PDF document cache
├── config/               # Centralized YAML data (asx_{module}.yaml)
│   ├── asx_analyzer.yaml       # Analyzer stock/ETF watchlists & scoring weights
│   ├── asx_announcements.yaml  # Announcements scanner output (auto-generated)
│   ├── asx_catalysts.yaml      # Catalyst radar stock database (manually curated)
│   └── asx_placements.yaml     # Placements scanner output (auto-generated)
│
├── templates/            # Centralized HTML templates (asx_{module}.html)
│   ├── asx_analyzer.html       # Technical trend dashboard template
│   ├── asx_announcements.html  # Announcements dashboard template
│   ├── asx_catalysts.html      # Catalyst radar template
│   └── asx_placements.html     # Placements dashboard template
│
├── output/               # All exported reports (HTML)
│   ├── asx_analyzer.html       # Technical trend leaderboard
│   ├── asx_announcements.html  # Announcements dashboard
│   ├── asx_catalysts.html      # Catalyst radar dashboard
│   └── asx_placements.html     # Placements dashboard
│
├── run.py                # Unified CLI runner
└── asx_sectors.md        # AI prompt documentation for the 11 ASX Core Sectors
```

> **Note**: All generated dashboards (`.html`) are automatically routed to the `output/` directory. Persistent tracking data and configuration files reside inside the `config/` directory using the `asx_{module}.yaml` naming convention.

## Modules

### 1. Catalyst Radar (`asx_catalysts`)
Compiles tracking information of high-conviction fundamental plays from `config/asx_catalysts.yaml` and builds an interactive HTML radar sorted by event timeline, probability, and execution risk.

### 2. Market Analyzer (`asx_analyzer`)
Pulls Yahoo Finance data for a predefined set of tickers listed in `config/asx_analyzer.yaml`. Performs technical factor ranking (SMA, Momentum, Volatility, RSI) and outputs a scored HTML interactive leaderboard.

### 3. Price-Sensitive Announcements Scanner (`asx_announcements`)
Directly polls the ASX MarkIt API for strictly price-sensitive news over a specified lookback timeframe. Uses multi-threaded parsing (`pdfplumber`) alongside keyword extraction to build summarized datasets. Outputs YAML (`config/asx_announcements.yaml`) + styled HTML dashboard.

### 4. Placements & Capital Raisings (`asx_placements`)
Targeted pipeline looking for new capital issues (placements, SPP). Extracts issuance prices out of PDFs, fetches real-time ticker prices concurrently, and computes the discount/premium % for immediate arbitrage detection. Outputs YAML (`config/asx_placements.yaml`) + styled HTML dashboard.

## Unified CLI

```bash
python run.py catalysts          # Generate Catalyst Radar HTML
python run.py analyzer           # Run Technical Trend Analyzer (HTML)
python run.py announcements      # Scan → YAML + HTML
python run.py placements         # Scan → YAML + HTML
python run.py dashboard          # Regenerate unified dashboard FROM existing YAML cache
python run.py all                # Full re-scan and update EVERYTHING (all 4 modules)
```

## Refined Experience

- **Clean CLI Output**: All modules now feature a standardized, non-distracting console interface with dimmed progress logs and clear success notifications.
- **Unified Dashboard**: The `run.py dashboard` command creates a single, integrated HTML view combining all four research modules into one screen.
- **Optimized Storage**: Modules like `asx_analyzer` use a compact YAML format to store metadata and results together, keeping the `config/` directory clean.

## Data Pipeline

```
ASX API → Scanners (asx_announcements.py / asx_placements.py)
              ├── config/asx_*.yaml     (Centralized tracking DB)
              └── output/*.html         (Styled dashboard)

yFinance → Analyzer (asx_analyzer.py)
              └── config/asx_analyzer.yaml (Merges results into config)
```

> **Optimization**: The `asx_analyzer` now uses a compact, single-line-per-entry YAML format within the primary `config/asx_analyzer.yaml` file to store both static metadata and dynamic results, eliminating redundant cache files.
