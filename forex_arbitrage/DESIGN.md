# Triangular Forex Arbitrage Detector

Detect profit opportunities in triangular currency exchange between major forex currencies.

## 1. Requirements

**Scope**: Build a tool that detects triangular arbitrage opportunities among major forex currencies.

**Deliverables**:
- Python script that fetches live exchange rates
- Detect all profitable currency trios (e.g., USD → AUD → EUR → USD)
- Display profit percentage for each opportunity

**Success Criteria**:
- Correctly identify when exchanging through 3 currencies yields more than direct exchange
- Support major currencies: USD, EUR, GBP, JPY, AUD, CAD, CHF, NZD

---

## 2. Technology Stack

| Component | Technology | Justification |
|-----------|------------|---------------|
| Language | Python 3.x | Simple, good for prototyping |
| HTTP Client | `requests` | Standard, easy to use |
| Exchange Rates API | Free forex API (e.g., exchangerate-api.com, frankfurter.app) | Free tier available |

---

## 3. Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Exchange Rate  │────▶│  Rate Matrix     │────▶│  Arbitrage      │
│  API            │     │  Builder         │     │  Detector       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │  Results        │
                                                 │  Display        │
                                                 └─────────────────┘
```

**Algorithm**:
1. Fetch exchange rates for all major currency pairs
2. Build a rate matrix (currency A → currency B)
3. For each trio (A → B → C → A), calculate: `rate(A→B) × rate(B→C) × rate(C→A)`
4. If result > 1.0, arbitrage opportunity exists (profit = result - 1)

---

## 4. Task Breakdown

| # | Task | Estimate |
|---|------|----------|
| 1 | Set up project structure | 10 min |
| 2 | Implement exchange rate fetcher | 30 min |
| 3 | Build rate matrix from API response | 20 min |
| 4 | Implement triangular arbitrage detection | 30 min |
| 5 | Format and display results | 20 min |
| 6 | Add error handling and logging | 15 min |
| 7 | Testing and validation | 20 min |

---

## 5. Quality

**Testing Strategy**:
- Unit tests for arbitrage calculation logic
- Mock API responses for consistent testing
- Manual verification against known exchange rates

**Example Test Case**:
```
If USD→EUR = 0.92, EUR→GBP = 0.86, GBP→USD = 1.27
Product = 0.92 × 0.86 × 1.27 = 1.005
Profit = 0.5% (arbitrage exists)
```

---

## 6. Risk Management

| Risk | Mitigation |
|------|------------|
| API rate limits | Cache responses, use free tier wisely |
| Stale rates | Display timestamp, refresh on demand |
| False positives | Account for transaction fees (configurable threshold) |

---

## 7. Usage Example

```bash
python arbitrage_detector.py

# Output:
# Scanning 8 major currencies for arbitrage opportunities...
# 
# ✓ USD → AUD → EUR → USD : +0.15% profit
# ✓ GBP → JPY → CHF → GBP : +0.08% profit
# 
# No opportunities: 54 trios checked
```

---

## 8. File Structure

```
forex_arbitrage/
├── arbitrage_detector.py   # Main script
├── rates_fetcher.py        # API integration
├── test_arbitrage.py       # Unit tests
└── README.md               # Usage instructions
```
