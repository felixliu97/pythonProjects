# ASX Placement / Capital Raising Scanner

Scans ASX announcements for capital raising, placement, SPP, and rights issue events. Downloads PDFs to extract price, quantity, and amount raised. Supports incremental scanning by resuming from the last date in the existing CSV.

## Quick Start

```bash
pip install requests pdfplumber

# Full scan with parallel PDF extraction (10 threads)
python asx_placements.py

# Fast scan without PDF extraction
python asx_placements.py --no-pdf

# Custom lookback period
python asx_placements.py --months 3

# Price-sensitive announcements only
python asx_placements.py --price-sensitive
```

## How It Works

1. **Fetch Announcements** — Calls the ASX MarkIt Digital API (`asx.api.markitdigital.com/asx-research/1.0/markets/announcements`) for "issued capital" announcements over the specified lookback period.
2. **Filter** — Keeps announcements matching placement/capital-raise keywords in the headline or announcement types while ignoring administrative noise (e.g., "Cleansing Notice").
3. **Download** — Multi-threaded (10 threads) PDF download via CDN (`cdn-api.markitdigital.com`), with delta caching (skips already-downloaded files).
4. **Extract Data** — Extracts financial data using a two-tier approach:
   - **PDF Text via Regex**: Parses the first 5 pages for placement price, shares issued, and amount raised.
   - **Headline Fallback**: If PDF extraction fails, extracts amount and price directly from the announcement headline.
5. **Fetch Current Price & Info** — Calls the ASX MarkIt Digital Company API (`/companies/{symbol}/header`) to fetch the real-time stock price and company name (`displayName`) for all matched and existing symbols concurrently. This passively backfills any missing company names natively without relying on a separate script.
6. **Output** — Calculates the percentage difference between the placement price and the current market price, prints a JSON summary, and exports `asx_placements.csv`.

## Extraction Logic (Field by Field)

The data required for the final output combines basic properties returned in the API responses and financial values processed out of the attached PDFs. Each output column is populated via the following extraction logic:

- **`ASX_Code`**: Direct map from the `symbol` key in the announcement JSON list.
- **`Company`**: Direct map from the nested `companyInfo[0].displayName` key in the announcement JSON.
- **`Headline`**: Direct map from the `headline` key in the announcement JSON.
- **`Date`**: Parsed from the ISO string `date` key in the API response, formatted as `YYYY-MM-DD`.
- **`PDF_Link`**: Constructed dynamically by taking the announcement's `documentKey` and appending it to `https://cdn-api.markitdigital.com/apiman-gateway/ASX/asx-research/1.0/file/{docKey}?access_token={token}`.
- **`Current_Price`**: Pulled via a secondary HTTP GET request to `https://asx.api.markitdigital.com/asx-research/1.0/companies/{symbol}/header`. The script targets `data.priceLast`. This same endpoint is also used to passively fill missing `Company` values via `data.displayName`.

### Distilling Financial Data (PDF & Headline Fallback)
Financial fields use a sequential pipeline logic. They are first sought inside the downloaded PDF text (Pages 1-5 exclusively); if the PDF parsing fails—or is bypassed via `--no-pdf`—the script attempts a headline fallback.

- **`CR_Price`**:
  - **PDF Regex**: Targets explicit per-share valuation syntaxes such as `A$X.XX per share`, `@ $X.XX`, `issue price of $X.XX`. Also handles word-based phrasing like `X cents per share` or `X dollars per share`.
  - **Headline Fallback**: Looks for isolated `$X.XX` figures in the headline string not directly attached to words like `million` or `m`.
- **`Shares_Issued`**:
  - **PDF Regex**: Heavily dependent on positional matching against keywords like `new fully paid ordinary shares` or `number of securities: X`. Scans for pure comma-delimited integers (e.g., `50,000,000`) or textual shorthands (e.g., `34.5 million`).
  - **Headline Fallback**: Not supported; only available via PDF extraction.
- **`Amount_Raised`**:
  - **PDF Regex**: Identifies large capitalization figures (e.g., `A$55 million`, `$20m`) within character proximity of anchor verbs (`raising`, `raised`, `gross proceeds`) or the word `placement`.
  - **Headline Fallback**: Extracts large capital figures ending in `M`, `m`, or `<value> million`. Also acts as a safety net catching raw integer values `>= $100,000` (assuming these are aggregate capital inputs, not per-share prices).

- **`Price_Diff_%`**:
  - A mathematically derived field. Formula: `((Current_Price - Placement_Price) / Placement_Price) * 100`. Relies on safely casting `CR_Price` and `Current_Price` string representations into Python floats.

### 3. Real-Time Price & Company Info Integration
To evaluate the placement's discount/premium, the script queries the live ASX API for the `priceLast` and `displayName` fields using up to 20 concurrent threads. It deduplicates API calls by symbol to optimize network usage, passively populates any blank company names, and then calculates:
`Price_Diff_% = ((Current_Price - Placement_Price) / Placement_Price) * 100`

### API Endpoints Used
- **Announcements**: `https://asx.api.markitdigital.com/asx-research/1.0/markets/announcements`
- **Current Price**: `https://asx.api.markitdigital.com/asx-research/1.0/companies/{symbol}/header`
- **PDF CDN Proxy**: `https://cdn-api.markitdigital.com/apiman-gateway/ASX/asx-research/1.0/file/{docKey}?access_token={token}`

## PDF Caching

- PDFs are cached in the shared `../.pdf_cache/` directory with naming: `{Date}_[{ASX_CODE}]_{Headline_Clean}.pdf` (e.g. `2026-03-19_[1AD]_New AD-214 patent granted.pdf`)
- Re-runs only download **new** announcements (delta caching)
- Cached PDFs are read from disk without network calls

## Output Columns
**Requirement:** All extracted values must be strictly correct and valid.

| Column | Description |
|--------|-------------|
| `ASX_Code` | Ticker symbol |
| `Company` | Company name |
| `Headline` | Announcement headline |
| `Date` | Announcement date |
| `CR_Price` | Placement price per share (raw numeric, e.g. `0.086` not `$0.086`). Must be sortable as a number. |
| `Current_Price` | Current real-time price from the ASX API (raw numeric, e.g. `0.086` not `$0.086`). Must be sortable as a number. |
| `Price_Diff_%` | Percentage difference between placement price and current price (raw float, e.g. `-11.6` not `-11.6%`). Must be sortable as a number. |
| `PDF_Link` | Direct clickable URL to the announcement PDF. Must be a valid, openable HTTP link. |

## Keywords Matched

- **Placement Keywords**: `placement`, `capital rais`, `capital raise`, `share purchase plan`, `SPP`, `rights issue`, `entitlement offer`, `equity rais`, `equity raise`, `pro rata`, `non-renounceable`, `renounceable offer`
- **Noise Keywords (Ignored)**: `Cleansing Notice`, `Application for quotation`, `Appendix 2A`, `Change of Director`, `Results of Meeting`, `Notification of buy-back`
- **Reject Keywords (Excludes whole announcement)**: `acquisition`, `takeover`, `merger`, `exercise of options`, `conversion`, `dividend`, `buy-back`, `vesting`, `lapse`, `cancellation`

## Known Issues & Future Requirements

Based on sample runs resulting in `asx_placements.csv`, the current logic has several known limitations and requirements that must be addressed in future updates.

### Data Extraction Bugs
1. **Missed Extractions (Blank Values)**:
   - **`Shares_Issued`**: Frequently blank for several announcements. The regex patterns often miss the phrasing in the PDF if the amount isn't positioned near specific keywords like "ordinary shares" or "million".
   - **`CR_Price` and `Amount_Raised`**: Sometimes missed if the phrase relies heavily on table layouts rather than inline text, or if the headline format is non-standard.
2. **Incorrect Value Formatting (Unit Mismatch)**:
   - Exact, fully expanded numbers are sometimes incorrectly combined with the "M" suffix (e.g., `Amount_Raised` appearing as `$30,094,623M`). The logic must distinguish between rounded decimal millions (e.g., "$30.1M") and exact figures.
3. **Value Misclassification & Extreme Outliers**:
   - The script can capture an unrelated dollar figure as the placement price. For example, a `CR_Price` of `$30,000` was captured for a security trading at `$0.01`. This usually happens when extracting a minimal subscription threshold (e.g., "minimum parcel of $30,000") instead of the per-share price. This produces severely distorted `Price_Diff_%` calculations (e.g., `-100.00%`).

### Core Requirements for Future Updates
1. **Absolute Data Accuracy**:
   - Any script enhancements **MUST** rigorously ensure that all extracted values (especially `CR_Price`, `Shares_Issued`, and `Amount_Raised`) are accurate and represent the true values of the placement. Misclassifications and blank fields where data genuinely exists must be aggressively eliminated.
2. **Strict Deduplication (Preserve Original)**:
   - The output must contain exactly **one row per stock**. If a stock already exists in the CSV, the script strictly ignores any new placement announcements for that stock, securely preserving the original placement row while continuously updating its `Current_Price`, `Price_Diff_%`, and any missing `Company` values.
3. **Aggressive Multithreading**:
   - Future updates should aggressively utilize multi-threading wherever possible—especially for network-bound I/O like fetching announcements, downloading PDFs, extracting text, and pulling current prices—to drastically minimize overall execution time.
## Incremental Scanning & Append Mode

By default, the script operates in **incremental mode**:

1. **Read Existing CSV** — On startup, read `asx_placements.csv` to determine the maximum `Date` value.
2. **Determine Start Date** — Set the API query start date to `max_date + 1 day`. If that date is in the future (i.e. CSV is already up to date), skip the scan and exit with a message.
3. **Deduplicate Against Existing** — Build a set of `(ASX_Code, Date)` keys from the existing CSV. Skip any API results that already exist.
4. **Append New Rows** — Append only new rows to the CSV (no header rewrite, no overwriting existing data).
5. **`--full-refresh` Flag** — When passed, ignore the existing CSV entirely and perform a full re-scan using `--months` as the lookback period. This **overwrites** the CSV.
6. **First Run** — If no CSV exists, behave as a full scan using `--months` (default 2) and create the CSV with a header row.
