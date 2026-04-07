# ASX Placement / Capital Raising Scanner

Scans ASX announcements for capital raising, placement, SPP, and rights issue events. Downloads PDFs to extract price, quantity, and amount raised. Supports incremental scanning by resuming from the last date in the existing YAML.

## Quick Start

```bash
pip install requests pdfplumber pyyaml

# Full pipeline: scan → YAML + HTML
python run.py placements

# Fast scan without PDF extraction
python run.py placements --no-pdf

# Custom lookback period
python run.py placements --months 3

# Re-generate HTML from latest YAML (cached)
python run.py placements --html-only
```

## Output Pipeline

```
ASX API → asx_placements.py
              ├── config/asx_placements.yaml      (structured YAML tracking DB)
              └── output/asx_placements.html      (styled dashboard natively generated)
```

## How It Works

1. **Fetch Announcements** — Calls the ASX MarkIt Digital API for "issued capital" announcements over the specified lookback period.
2. **Filter** — Keeps announcements matching placement/capital-raise keywords in the headline while ignoring administrative noise (e.g., "Cleansing Notice").
3. **Download** — Multi-threaded (10 threads) PDF download via CDN, with delta caching (skips already-downloaded files).
4. **Extract Data** — Extracts financial data using a two-tier approach:
   - **PDF Text via Regex**: Parses the first 5 pages for placement price, shares issued, and amount raised.
   - **Headline Fallback**: If PDF extraction fails, extracts amount and price directly from the announcement headline.
5. **Fetch Current Price & Info** — Calls the ASX MarkIt Digital Company API to fetch the real-time stock price and company name for all matched symbols concurrently.
6. **Export** — Outputs:
   - `config/asx_placements.yaml` — Structured YAML acting as primary database
   - `output/asx_placements.html` — Styled HTML dashboard (generated natively at end of scan)

## Output Columns

| Column | Description |
|--------|-------------|
| `ASX_Code` | Ticker symbol |
| `Company` | Company name |
| `Headline` | Announcement headline |
| `Date` | Announcement date |
| `CR_Price` | Placement price per share (numeric float in YAML) |
| `Current_Price` | Current real-time price from the ASX API (raw numeric) |
| `Price_Diff_%` | Percentage difference between placement price and current price |
| `PDF_Link` | Direct clickable URL to the announcement PDF |

## HTML Dashboard Features

- Price diff color coding: green (premium), red (discount), grey (N/A)
- Date color coding: Today (green), Recent 7 days (orange), Older (grey)
- All headlines styled as `.e-cr` placement pills
- Top 10 ranking by post-placement performance
- Follows the `asx_catalysts.html` visual design standard

## Extraction Logic

- **`CR_Price`**: PDF regex targets `A$X.XX per share`, `@ $X.XX`, `issue price of $X.XX`. Headline fallback for isolated `$X.XX` figures.
- **`Shares_Issued`**: PDF regex matches `new fully paid ordinary shares` or `number of securities: X`.
- **`Amount_Raised`**: PDF regex identifies large figures near anchor verbs (`raising`, `raised`, `gross proceeds`).
- **`Price_Diff_%`**: `((Current_Price - CR_Price) / CR_Price) * 100`

## Keywords

- **Placement Keywords**: `placement`, `capital rais`, `share purchase plan`, `SPP`, `rights issue`, `entitlement offer`, `equity rais`, `pro rata`, `non-renounceable`, `renounceable offer`
- **Noise Keywords (Ignored)**: `Cleansing Notice`, `Application for quotation`, `Appendix 2A`, `Change of Director`
- **Reject Keywords**: `acquisition`, `takeover`, `merger`, `exercise of options`, `conversion`, `dividend`, `buy-back`

## PDF Caching

- PDFs are cached in the shared `../.pdf_cache/` directory with naming: `{Date}_[{ASX_CODE}]_{Headline_Clean}.pdf`
- Re-runs only download **new** announcements (delta caching)

## Incremental Scanning & Append Mode

1. **Read Existing YAML** — On startup, read `config/asx_placements.yaml` to determine the maximum `Date` value recorded.
2. **Determine Start Date** — Set the API query start date to `max_date + 1 day`. If in the future, skip.
3. **Deduplicate Against Existing** — Build a set of `(ASX_Code, Date)` keys from the active YAML.
4. **Append New Rows** — Append only new rows combining with historic rows.
5. **`--full-refresh` Flag** — Ignore existing tracking database, perform full re-scan.
