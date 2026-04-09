# ASX Announcements Scanner

Scans ASX announcements for **price-sensitive** events. The system downloads PDFs to a shared cache, extracts text, and generates summaries for the unified dashboard.

## Quick Start

```bash
# Full pipeline: scan and update dashboard
python run.py announcements

# Fast scan without PDF extraction (just headlines)
python run.py announcements --no-pdf

# Custom lookback period (default 1 month)
python run.py announcements --months 3
```

## Directory Structure

```text
asx_announcements/
├── asx_announcements.py   # Price-sensitive news crawler
└── README.md              # Technical documentation
```

## How It Works

1. **Fetch Price-Sensitive Announcements** — Directly requests `priceSensitiveOnly=true` announcements from the ASX MarkIt Digital API.
2. **Local PDF Verification** — Scans existing PDFs in the shared `../.pdf_cache/` directory. If missing, dynamically downloads from the ASX CDN.
3. **Extract & Summarize** — Uses `pdfplumber` to pull the first several paragraphs of the PDF into a concise string format.
4. **Data Engine Export** — Outputs:
   - `config/asx_announcements.yaml` — Persistent local history.
   - `output/asx_announcements.json` — Ingested by the unified dashboard.

## Data Retention Policy

To keep the newsfeed high-signal and high-speed:
- The module automatically purges records older than **7 days** during each run.
- Deduplication ensures that existing announcements in the `config/` database are not re-processed.

> [!IMPORTANT]
> This module operates in **Headless Mode**. All UI rendering is handled by the Unified Dashboard at `output/asx_dashboard.html`.
