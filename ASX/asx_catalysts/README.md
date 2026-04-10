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
- **Probability Score** (Primary): 极高 > 高 > 中高 > 中 > 中低 > 低
- **CR Risk Score** (Secondary): 极低 > 低 > 中 > 中高 > 高 > 极高
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
作为一个资深的 ASX 市场分析师，请根据最新的公告数据更新 `asx_catalysts.yaml` 中的催化剂概况。

你的任务是**在不添加任何新股票的前提下**更新现有标的的最新动态。请对比最新的 ASX 公告数据（特别是针对 Growth 组的 Tickers），如有重大里程碑进展或风险变化，请按照以下标准更新 `asx_catalysts.yaml` 内容：

具体更新要求：
1. **遵循严格的 YAML Schema**：保持现有的层级结构，确保缩进、列表格式与原文件完全一致。
2. **新增近期已发生的核心催化剂/风险**：如果是过去 1-3 个月内发生的重大事件（如临床数据发布、项目 FID、大规模钻探发现等），请在 `Catalysts` 和 `Timeline` 节点中补充。
3. **校准融资风险 (CR_Risk) 与成功概率 (Probability)**：根据最新的 4C/4D/5B 财报现金流状况，以及过去 12 个月的进展力度，实时调整相关评级及核心备注。
4. **简洁的核心备注 (Core_Notes)**：更新核心投资逻辑，突出该标的的独特性与近期博弈点。
```
