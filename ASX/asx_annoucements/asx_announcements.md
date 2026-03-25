# ASX Price Sensitive Announcements Scanner

Scans ASX announcements for **price-sensitive** events, filters by positive keywords (e.g. offtake agreements, major contracts signed, strategic partnerships, significant discoveries). The system downloads the associated announcement PDFs to a shared `../.pdf_cache/` folder, extracts the text, and processes the content to generate short summaries.

## Quick Start

```bash
pip install requests pdfplumber pandas

# Full scan with parallel PDF extraction (10 threads)
python asx_announcements.py

# Fast scan without PDF extraction
python asx_announcements.py --no-pdf

# Custom lookback period
python asx_announcements.py --months 3
```

## How It Works

1. **Fetch Price-Sensitive Announcements** — Directly requests ONLY `priceSensitiveOnly=true` announcements from the ASX MarkIt Digital API up to the current completion day.
2. **Filter** — Keeps announcements matching broadly positive keywords in the headline (e.g., "offtake", "discovery", "drilling results", "assay"). Administrative noise is strictly ignored.
3. **Local PDF Verification** — Scans existing PDFs in the shared `../.pdf_cache/` directory (e.g. `2026-03-24_[BTR]_High_grade_results.pdf`). If missing, dynamically downloads it over CDN concurrently.
4. **Extract & Summarize** — Uses `pdfplumber` to pull the first several paragraphs of the PDF into a concise string format.
5. **Uniform Company Identification** — Triggers isolated asynchronous queries directly to the ASX headers API to resolve flawless company names for all symbols.
6. **Output** — Exports the final unified dataset directly to `asx_price_sensitive_announcements.csv`.

## Output Format
The script outputs a CSV file (`asx_price_sensitive_announcements.csv`) with the highly condensed columns:

| Column | Description |
|--------|-------------|
| `ASX_Code` | Ticker symbol |
| `Company` | Authoritative Company Name fetched uniformly |
| `Headline` | Announcement headline |
| `Date` | Announcement date |
| `Summary` | Extracted overview of the positive announcement |
| `PDF_Link` | Direct clickable URL |

## Incremental Scanning & Append Mode

1. **Read Existing CSV** — On startup, read `asx_price_sensitive_announcements.csv` to determine the maximum `Date` value log.
2. **Determine Start Date** — Set the API query start date to `max_date + 1 day`.
3. **Deduplicate Against Existing** — Build a set from the active CSV. Skip API results that already exist locally.
4. **Append New Rows** — Fetch uniform names for the new set combined with historical lines and rewrite.
