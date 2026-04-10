# ASX Market Analysis & Research Suite

A high-performance, unified Python ecosystem for Australian Securities Exchange (ASX) data extraction, multi-dimensional market analysis, and fundamental catalyst tracking.

This project is designed with a **Headless Data Engine** architecture: individual specialized engines process raw market data into structured JSON/YAML, which is then rendered by a responsive, Pro-grade Jinja2 dashboard.

---

## 🏗 Project Architecture & Data Flow

### Directory Structure
```text
ASX/
│
├── scripts/              # Technology Data Engines (Headless Processors)
│   ├── asx_analyzer.py         # Technical Screener (Momentum/Volume/RSI)
│   ├── asx_announcements.py    # Price-Sensitive News Crawler & AI Summarizer
│   ├── asx_catalysts.py        # Fundamental Catalyst Radar Engine
│   └── asx_placements.py       # Capital Raising Discovery & PDF Extractor
│
├── config/               # Persistent Databases (Source of Truth)
│   ├── asx_analyzer.yaml       # Watchlist & Scoring Config
│   ├── asx_announcements.yaml  # Persistent history of price-sensitive news
│   ├── asx_catalysts.yaml      # Master Catalyst/Fundamental Database
│   ├── asx_placements.yaml     # Capital raising history & discovery DB
│   └── settings.yaml           # Global API endpoints & system settings
│
├── docs/                 # Research Documentation & Guides
│   └── asx_sectors.md          # ASX 11 Core Sectors strategic overview
│
├── templates/            # Presentation Layer (UI Source)
│   ├── asx_dashboard.html      # Unified Pro Dashboard (Jinja2)
│   └── base.css                # Modern Financial UI Styling
│
├── output/               # Production Build (UI + Data)
│   ├── asx_dashboard.html      # THE HUB (Open this to view all research)
│   └── *.json                  # Processed data ingested by the dashboard
│
├── .pdf_cache/           # Local cache for extracted announcement PDFs
├── run.py                # Unified CLI Runner (System Entry Point)
└── README.md             # Project Master Documentation

```

### Data Flow Pipeline
1. **Extraction**: Scripts fetch data from ASX MarkIt API, yFinance, and direct PDF CDNs.
2. **Processing**: Engines filter noise, calculate technical scores, and extract financial metrics.
3. **Persistence**: Validated data is stored in `config/*.yaml` (Human-readable DB).
4. **Export**: Data is exported to `output/*.json` for high-speed dashboard ingestion.
5. **Rendering**: `run.py` uses Jinja2 to merge JSON data with `asx_dashboard.html` to produce the final interactive report.

---

## 🛠 Technical Specifications & Requirements

### Dependencies
- **Core**: `Python 3.9+`
- **Data Acquisition**: `requests`, `yfinance`
- **Data Processing**: `PyYAML`, `json`, `datetime`, `re` (Regex)
- **PDF Extraction**: `pdfplumber` (Crucial for Announcements & Placements)
- **UI Rendering**: `Jinja2`

### Requirements
- Active internet connection for API access.
- `pdfplumber` must be installed for summary extraction logic to function.
- Standard libraries: `concurrent.futures` (Threading), `collections` (Counter).

---

## 📊 Core Data Engines (Deep Dive)

### 1. Market Momentum Analyzer (`asx_analyzer.py`)
Computes a proprietary **Momentum Score (0-100)** for three categories: Growth Stocks, Foundation Stocks, and ETFs.

- **Weighting Logic**:
  - `1D Price Change` (30%): Immediate volatility response.
  - `5D Price Change` (25%): Weekly trend reinforcement.
  - `20D Price Change` (15%): Monthly baseline trend.
  - `Volume Surge` (20%): `(Current / 20D Avg Vol) - 1`. **Capped at 400%** to filter out anomalous penny stock manipulations.
  - `Trend (RSI)` (10%): `(RSI - 50)` divergence.
- **Risk Calculation**: Displays annualized standard deviation of returns (Volatility).

### 2. Catalyst Radar (`asx_catalysts`)

Tracking engine for high-conviction fundamental plays and market catalysts.

#### Risk-Reward Sorting Logic
- **Primary**: Probability Score (极高 > 高 > 中高 > 中 > 中低 > 低)
- **Secondary**: CR Risk Score (极低 > 低 > 中 > 中高 > 高 > 极高)

#### Master Catalyst Timeline
Aggregates future-looking "Key Catalysts" from all stocks into a single chronological feed. It filters specifically for catalysts with explicit timeframes (e.g., "2026 Q2", "2026 May") to provide a forward-looking market roadmap.

### 3. Announcements Scanner (`asx_announcements.py`)
A continuous monitor for market-moving events.

- **Deduplication**: Uses a `Symbol_Date_Headline` composite key to prevent redundant processing.
- **AI Summary Extraction**: Downloads PDFs from the ASX CDN, uses `pdfplumber` to extract text, and filters out administrative noise (noise filter includes trading halts, cleansing notices, etc.).
- **Impact Rating (1-5)**: Keyword-driven logic assigns a rating based on terms like "Discovery", "High-Grade", "Billion", "Award", or "Termination".

### 4. Placements Scanner (`asx_placements.py`)
A specialized pipeline for capital raising arbitrage and dilution tracking.

- **Regex Pricing Extraction**: Scans PDF text for pricing patterns (e.g., `at $0.05 per share` or `at 5 cents per security`).
- **Discount Detection**: Fetches live prices concurrently for comparison against issuance prices.
- **Liquidity Guard**: Automatically rejects stocks with `Market Cap < $10M` or `Daily Value < $20k` to ensure researchers focus on tradable entities.

---

## 💾 Data Structures (Database Specs)

### `config/asx_catalysts.yaml` (Master Fundamental DB)
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `Ticker` | string | Yes | ASX symbol (e.g., "IMU") |
| `Sector` | string | Yes | Industry/Play description |
| `CR_Risk` | string | Yes | Capital raising risk rating (Chinese labels) |
| `Probability` | string | Yes | Success probability rating (Chinese labels) |
| `Catalysts` | list | No | Max 5 upcoming high-impact events |
| `Timeline` | list | No | List of `Time` and `Event` historical milestones |
| `Core_Notes`| string | No| Detailed multi-line investment thesis |

### `config/asx_analyzer.yaml` (Technical Watchlist)
- `growth_stocks`: Symbols where Momentum Score is prioritized.
- `foundation_stocks`: Large-cap symbols where stability is key.
- `etfs`: Diversified instruments.
- `weights`: Global config for scoring calculation parameters.

---

## 🚀 Operations & Maintenance

### Unified CLI Entry Point
The system should always be navigated via `run.py`:
```bash
python run.py all              # THE FULL RESET: Re-scans everything and updates UI
python run.py analyzer --force # Force a fresh market data pull (ignore cache)
python run.py announcements    # Quick scan for new price-sensitive news
python run.py placements       # Refresh capital raising data
python run.py dashboard        # Update UI layout without fetching new data
```

### AI-Assisted Maintenance
To update the project with new catalysts, feed `asx_catalysts.yaml` to an AI with this instruction:
> "Analyze recent ASX announcements and update the `Catalysts`, `Timeline`, and `CR_Risk` for the existing tickers in the provided YAML. Do not add new tickers. Ensure the Chinese rating labels (极高/高/中/低) are preserved."

---

## 🎨 Presentation Layer
The dashboard uses **DataTables.js** for interactive sorting and search.
- **Color Correction**: Visual indicators for price action (Positive: Green, Negative: Red, Neutral: Dim).
- **Sparklines**: Integrated price action micro-charts.
- **Precision**: Price and Difference values are tracked to **3 decimal places** (`trim_zeros` filter applied to hide non-significant trailing zeros).

---

## 📚 Supporting Documentation
Additional research guides and sector-specific knowledge items are maintained in the `/docs` directory:
- [ASX 11 Core Sectors Overview](file:///e:/repos/pythonProjects/asx/docs/asx_sectors.md): Strategic background for AI analysis across key market segments.

