# ASX Market Momentum Analyzer

Advanced technical screening engine that pulls live market data via `yfinance` and calculates proprietary momentum scores for a curated list of ASX tickers.

## Quick Start

```bash
# Full pipeline: scan and update dashboard
python run.py analyzer

# Bypass cache and force a fresh data pull
python run.py analyzer --force
```

## Directory Structure

```text
asx_analyzer/
├── asx_analyzer.py    # The core analysis engine
└── README.md          # Technical documentation
```

## Momentum Scoring Algorithm (100-Point Scale)

The `ASXTrendingStocks` engine calculates a weighted score based on five key technical dimensions:

- **1D Price Change** (30%): Immediate price action.
- **5D Price Change** (25%): Weekly trend momentum.
- **20D Price Change** (15%): Monthly trend anchor.
- **Volume Surge (volume_change)** (20%): `(Current / Average Vol) - 1`. **Note: Capped at maximum 400%** to prevent anomalous penny stock volume spikes from blindly dictating the score.
- **Mom / Trend (momentum)** (10%): `(RSI - 50)`. Uses relative divergence instead of redundant raw price action.

> [!IMPORTANT]  
> **Clarification: `volume_change` vs `volatility`**
> - **`volume_change` (Volume Surge):** The calculated percentage spike in daily trading volume vs historical average. Used *strictly internally* to calculate the momentum score.
> - **`volatility` (Displayed as Risk/Volatility):** The annualized standard deviation of historic daily price returns. Placed strictly in the dashboard as an *informational display column*, and is **NOT** used to calculate the score.

## Output

This module operates as a **Headless Data Engine**:
1. Processes market data for all configured tickers in `config/asx_analyzer.yaml`.
2. Exports structured research to `output/asx_analyzer.json`.
3. Automatically triggers a dashboard refresh via `run.py`.

> [!NOTE]
> The analyzer handles data sanitization (filtering out infinity/NaN values) to ensure dashboard stability.
