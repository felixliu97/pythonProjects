# ASX Price Sensitive Announcements Scanner

Scans ASX announcements for **price-sensitive** events, filters by positive keywords (e.g. offtake agreements, major contracts signed, strategic partnerships, significant discoveries). The system downloads the associated announcement PDFs to a shared `../.pdf_cache/` folder, extracts the text, and processes the content to generate short summaries.

## Quick Start

```bash
pip install requests pdfplumber pyyaml

# Full pipeline: scan → YAML + HTML
python run.py announcements

# Fast scan without PDF extraction
python run.py announcements --no-pdf

# Custom lookback period
python run.py announcements --months 3

# Re-generate HTML from existing YAML (no API calls)
python run.py announcements-html
```

## Output Pipeline

```
ASX API → asx_announcements.py
              ├── config/asx_announcements.yaml      (structured YAML tracking DB)
              └── output/asx_announcements.html      (styled dashboard natively generated)
```

## How It Works

1. **Fetch Price-Sensitive Announcements** — Directly requests ONLY `priceSensitiveOnly=true` announcements from the ASX MarkIt Digital API up to the current completion day.
2. **Filter** — Keeps announcements matching broadly positive keywords in the headline (e.g., "offtake", "discovery", "drilling results", "assay"). Administrative noise is strictly ignored.
3. **Local PDF Verification** — Scans existing PDFs in the shared `../.pdf_cache/` directory. If missing, dynamically downloads it over CDN concurrently.
4. **Extract & Summarize** — Uses `pdfplumber` to pull the first several paragraphs of the PDF into a concise string format.
5. **Uniform Company Identification** — Triggers isolated asynchronous queries directly to the ASX headers API to resolve flawless company names for all symbols.
6. **Export** — Outputs:
   - `config/asx_announcements.yaml` — Structured YAML acting as primary database
   - `output/asx_announcements.html` — Styled HTML dashboard (generated natively at end of scan)

## Output Columns

| Column | Description |
|--------|-------------|
| `ASX_Code` | Ticker symbol |
| `Company` | Authoritative Company Name fetched uniformly |
| `Headline` | Announcement headline |
| `Date` | Announcement date |
| `Summary` | Extracted overview of the positive announcement |
| `PDF_Link` | Direct clickable URL |

## HTML Dashboard Features

- Date color coding: Today (green), Recent 7 days (orange), Older (grey)
- Headline pills auto-classified by type (drill/result/corporate/CR/milestone)
- Active stock ranking by announcement frequency
- Follows the `asx_catalysts.html` visual design standard

## Incremental Scanning & Append Mode

1. **Read Existing YAML** — On startup, read `config/asx_announcements.yaml` to determine the maximum `Date` value recorded.
2. **Determine Start Date** — Set the API query start date to `max_date`. This ensures that if the script is run multiple times on the same day, any new announcements released after the first run are correctly captured.
3. **Deduplicate Against Existing** — Build a set from the active YAML. Skip API results that already exist locally.
4. **Append New Rows** — Fetch uniform names for the new set combined with historical lines and rewrite.
