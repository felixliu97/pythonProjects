# Catalyst Radar HTML Generator

Automatically parses the curated stock database `config/asx_catalysts.yaml` and generates the `output/asx_catalysts.html` catalyst radar dashboard.

## Quick Start

```bash
pip install pyyaml

python run.py catalysts
```

## Directory Structure

```text
ASX/
├── asx_catalysts/
│   ├── asx_catalysts.py              # The build script
│   └── README.md                     # This document
├── config/asx_catalysts.yaml         # Single source of truth (YAML)
├── templates/asx_catalysts.html      # HTML template (CSS, Layout)
└── output/asx_catalysts.html         # Auto-generated dashboard
```

## Core Architecture

The system uses a **Data-Driven Templating** approach, entirely decoupling the data (YAML) from the presentation layer (HTML/CSS).

1. **The Generator (`asx_catalysts.py`)**: Reads YAML data and fills HTML placeholders.
2. **The Data Source**: `config/asx_catalysts.yaml` — a manually curated YAML database of tracked stocks.
3. **The Template**: `templates/radar_base_template.html` with `{{ table_rows }}` and `{{ breakout_html }}` placeholders.
4. **Rendering Logic**: Maps structured YAML properties into the radar HTML format with automatic CSS class assignment.

## Mapping Logic: Data → UI Classes

### A. Sector Tag Coloring (`Sector`)
- "PGM · Ti · V · Cu" → `s-pgm`
- "黄金/锑/钨" / "金铀钛" → `s-gold`
- "铜金" / "铜" → `s-copper`
- "铀" → `s-uranium`
- "石墨" → `s-critical`
- "生物能源" → `s-energy`
- "皮肤科" → `s-pharma`

### B. Event Pills (`Catalysts` & `Earnings_Window`)
- Contains "发布", "结果", "季报", "年报" → `e-result` (Blue)
- Contains "钻探", "Drill" → `e-drill` (Green)
- Contains "生产", "首气" → `e-production` (Light Green)
- Contains "融资", "入股", "并购" → `e-corporate` (Purple)
- Contains "重大", "已确认" → `e-hot` (Red/Pink)
- Default → `e-milestone` (Brown)

### C. Six-Month Heatmap (`Heatmap`)
- "Hot" → `mb-hot` (Deep Red: #B71C1C)
- "Active" → `mb-active` (Orange: #F57C00)
- "Watch" → `mb-watch` (Warm Yellow: #FFD54F)

### D. Probability Bar (`Probability`)
- "极高" → 95%, `p-vhigh` | "高" → 80%, `p-high` | "中高" → 65%, `p-mhigh`
- "中" → 50%, `p-med` | "中低" → 35%, `p-mlow` | "低" → 20%, `p-low`

## Sorting & Ordering

1. **Probability Score** (Primary): 极高 → 高 → 中高 → 中 → 中低 → 低
2. **Heatmap Hotness** (Secondary): Count of "Hot" months
3. **Alphabetical by Ticker** (Tertiary)

## YAML Data Schema

```yaml
- Ticker: string             # Required: Stock code (e.g., "TM1")
  Company: string            # Required: Full company name
  Sector: string             # Required: Sector tags
  Catalysts:                 # Required: Array of catalyst event strings
    - string
  Risks:                     # Optional: Array of risk event strings
    - string
  Earnings_Window:           # Required: Array of earnings window strings
    - string
  Heatmap:                   # Required: Exactly 6 month objects
    - Month: string          # e.g., "Apr", "May"
      Status: string         # "Hot" | "Active" | "Watch" | "Inactive"
      Reason: string         # Optional: Reason for status
  CR_Risk: string            # Required: Capital raising risk rating
  Probability: string        # Required: "极高" | "高" | "中高" | "中" | "中低" | "低"
  Core_Notes: string         # Required: Supports \n for linebreaks
  Timeline_Title: string     # Optional: Timeline header
  Timeline:                  # Optional: Array of timeline events
    - Time: string
      Event: string
```

## Development Workflow

1. Edit stock data in `config/asx_catalysts.yaml`
2. Run `python run.py catalysts`
3. Open `output/asx_catalysts.html` in a browser

## AI Analysis Prompt

To update the database using an AI assistant, copy the following prompt along with the `asx_catalysts.yaml` content:

```markdown
请充当资深的 ASX 澳洲小微盘资源股与生物科技分析师。我将向你提供我当前的 `asx_catalysts.yaml` 监控数据。

你的任务是：**利用你的实时联网检索能力，查询这批 ASX 股票（Tickers）的最新官方公告与市场动态，并为我返回一份全面更新后的 `asx_catalysts.yaml`。**

在更新时，请务必严格遵守以下核心指令：
1. **原样保持 YAML Schema**：严格维持现有的字段格式不可删减，确保返回的代码块可直接被 Python 加载。
2. **提炼与插入最新催化剂**：请检索这些公司在最近 1-3 个月发布的重大资讯，将它们新增或替换到 `Catalysts` 和 `Timeline` 列表中。
3. **滚动计算 Heatmap（热力图）**：基于此刻的真实月份，重新评估未来六个月的动态状态。
4. **动态重新评级**：依据最新的现金流报告评估 `CR_Risk`，校准 `Probability`，更新 `Core_Notes`。

请逐一检索列表中的这批股票，确保每一条更新的内容都确凿对应真实的 ASX 公告，不容发生幻觉。
```
