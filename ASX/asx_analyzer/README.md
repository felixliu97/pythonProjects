# ASX Market Analyzer

A multi-threaded technical analysis engine that identifies trending stocks and ETFs. It evaluates momentum using a combination of price action, volume spikes, and relative strength (RSI).

## Quick Start

```bash
# Process market data and refresh dashboard
python run.py analyzer
```

## Configuration

The application reads `config/asx_analyzer.yaml` for watchlists and scoring parameters.

**Key Config Sections:**
- `growth_stocks`: High-momentum, catalyst-driven opportunities.
- `foundation_stocks`: Stable, large-cap portfolio anchors.
- `etfs`: ETF ticker strings (e.g., `VAS.AX`).
- `weights`: Scoring weights for the 100-point algorithm.

## Scoring Algorithm

The "Momentum Score" is a hard-quantitative algorithm that prevents penny-stock outliers from destabilizing the ranks.

**Current Formula & Weights:**
- **1D Price Change** (30%): Near-term absolute velocity.
- **5D Price Change** (25%): Weekly confirmation pivot.
- **20D Price Change** (15%): Monthly trend anchor.
- **Volume Surge (volume_change)** (20%): `(Current / Average Vol) - 1`. **Note: Capped at maximum 400%** to prevent 10x anomalous penny stock volume spikes from blindly dictating the score.
- **Mom / Trend (momentum)** (10%): `(RSI - 50)`. Uses relative divergence instead of redundant raw price action.

> [!IMPORTANT]  
> **Clarification: `volume_change` vs `volatility`**
> - **`volume_change` (Volume Surge):** The calculated percentage spike in daily trading volume vs historical average. Used *strictly internally* to calculate the momentum score.
> - **`volatility` (Displayed as Risk/Volatility):** The annualized standard deviation of historic daily price returns. Placed strictly in the dashboard as an *informational display column*, and is **NOT** used to calculate the score.

## Output

This module operates as a **Headless Data Engine**:
1. Processes market data for all configured tickers.
2. Exports structured research to `output/asx_analyzer.json`.
3. Automatically triggers a dashboard refresh via `run.py`.

> [!NOTE]
> The analyzer handles data sanitization (filtering out infinity/NaN values) to ensure dashboard stability.
