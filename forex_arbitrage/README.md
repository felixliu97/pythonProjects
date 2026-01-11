# Triangular Forex Arbitrage Detector

Detects profit opportunities in triangular currency exchange between major forex currencies.

## Quick Start

```bash
# Install dependencies
pip install requests

# Run the detector
python arbitrage_detector.py
```

## How It Works

Triangular arbitrage exploits price discrepancies between three currencies:

```
USD → AUD → EUR → USD
```

If the product of exchange rates > 1.0, a profit opportunity exists.

## Configuration

- **Minimum Profit Threshold**: 0.05% (filters out negligible opportunities)

## Supported Currencies

USD, EUR, GBP, JPY, AUD, CAD, CHF, NZD
