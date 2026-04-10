# ASX Placements & Capital Raisings

Scans ASX announcements for capital raising events (placements, SPP, rights issues). It downloads PDFs to extract precise pricing details and compares them to real-time market data to identify discounts and premiums.

## Quick Start

```bash
# Full pipeline: scan and update dashboard
python run.py placements

# Fast scan without PDF extraction
python run.py placements --no-pdf

# Custom lookback period (default 1 month)
python run.py placements --months 3
```

## Directory Structure

```text
asx_placements/
├── asx_placements.py    # Capital raising scanner
└── README.md            # Technical documentation
```

## Data Precision

- **3-Decimal Pricing**: All placement prices and real-time prices are tracked to 3 decimal places (`$0.000`) to accurately capture cent-level discounts.

## How It Works

1. **Fetch Announcements** — Polls the ASX API for "issued capital" announcements.
2. **Intelligent Filtering** — Uses a keyword engine to separate actual placements from administrative noise (Cleansing Notices, Appendix 2A, etc.).
3. **Data Extraction** — 
   - **PDF Parsing**: Regex-based extraction of placement price from the shared PDF cache.
   - **Real-time Sync**: Fetches current share prices via the ASX Company API concurrently.
4. **Data Engine Export** — 
   - `config/asx_placements.yaml`: Persistent history and tracking DB.
   - `output/asx_placements.json`: Integrated into the unified dashboard.

## Incremental Scanning

The scanner automatically resumes from the last processed date in the `config/` database to avoid redundant API calls and processing. To perform a full re-scan, use the `--full-refresh` flag.

> [!NOTE]
> This module operates in **Headless Mode**. Results are visualized in the Unified Dashboard at `output/asx_dashboard.html`.
