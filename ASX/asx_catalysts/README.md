# ASX Catalyst Radar

Automated data engine for tracking high-conviction fundamental plays and market catalysts. It parses the curated `config/asx_catalysts.yaml` database and exports structured research for the unified dashboard.

## Quick Start

```bash
# Sync catalysts with dashboard
python run.py catalysts
```

## Directory Structure

```text
asx_catalysts/
├── asx_catalysts.py              # The data engine
└── README.md                     # This document
```

## Core Logic

### 1. Risk-Reward Sorting
The engine sorts stocks based on a sophisticated priority model:
- **Probability Score** (Primary): 极高 → 高 → 中高 → 中 → 低
- **CR Risk Score** (Secondary): 极低 → 低 → 中低 → 中 → 高 → 极高
- **Ticker** (Tertiary)

### 2. Time-Series Aggregation
Individual stock timelines are harvested and normalized to build the **Master Explosive Timeline** in the unified dashboard, allowing for a portfolio-wide view of upcoming market events.

### 3. Headless Export
The module exports all research to `output/asx_catalysts.json`. This JSON is then ingested by the Jinja2 template engine in the root directory to render the Pro Dashboard.

## YAML Schema

```yaml
- Ticker: string             # Stock code (e.g., "TM1")
  Company: string            # Full company name
  Sector: string             # Sector tags (e.g. "Critical Minerals")
  Catalysts: [string]        # Key catalyst events
  Risks: [string]            # Identified risks
  Earnings_Window: [string]  # Reporting dates
  CR_Risk: string            # Capital raising risk rating
  Probability: string        # Success probability
  Core_Notes: string         # Investment thesis
  Timeline:                  # Event nodes
    - Time: string           # Sortable date (YYYY-MM-DD or Qx)
      Event: string
```

## AI Analysis Prompt

To update the database using an AI assistant, copy the following prompt along with the `asx_catalysts.yaml` content:

```markdown
请充当资深的 ASX 澳洲小微盘资源股与生物科技分析师。我将向你提供我当前的 `asx_catalysts.yaml` 监控数据。

你的任务是：**利用你的实时联网检索能力，查询这批 ASX 股票（Tickers）的最新官方公告与市场动态，并为我返回一份全面更新后的 `asx_catalysts.yaml`。**

在更新时，请务必严格遵守以下核心指令：
1. **原样保持 YAML Schema**：严格维持现有的字段格式，严禁引入废弃字段。
2. **提炼与插入最新时刻表**：将最近 1-3 个月的重大资讯及即将到来的关键里程碑更新到 `Timeline` 列表中。
3. **校准爆发概率与风险控制**：基于最新的 4C/4D/5B 报告重新评估 `CR_Risk` 与 `Probability`，特别是现金余额对后续 12 个月运营的支撑能力。
4. **精炼核心逻辑 (Core_Notes)**：更新该股票当前最核心的投资叙事。
```
