# Catalyst Radar HTML Generator System Design

This document outlines the architecture for a dynamic HTML generator that automatically parses the individual stock JSON files stored in `stocks_json/` and reconstructs the `asx_catalyst_radar_6mo.html` visualization on the fly.

## 1. Directory Structure
```text
ASX/asx_catalysts/
├── stocks.yaml                       # Single source of truth (YAML list of objects)
├── templates/
│   └── radar_base_template.html      # Static HTML shell (CSS, Layout, Headers, Footers)
├── asx_catalyst_radar_6mo.md         # Documentation & Design
├── generate_radar.py                 # The build script
└── asx_catalyst_radar_6mo.html       # Auto-generated Output (Do not edit directly)
```

## 2. Core Architecture

The system uses a **Data-Driven Templating** approach, entirely decoupling the data (JSON) from the presentation layer (HTML/CSS).

1. **The Generator (`generate_radar.py`)**: A Python script utilizing the built-in `json` library and standard string formatting (or `Jinja2` for advanced templating).
2. **The Data Source**: Reads the single `stocks.yaml` file containing all stock definitions.
3. **The Template**: Reads `radar_base_template.html` which contains placeholder tags (e.g., `{{ table_rows }}` and `{{ timelines }}`).
4. **Rendering Logic**: Maps the structured JSON properties back into the specific radar HTML format.
5. **Responsive Layout**: The template CSS strictly uses `word-break: break-word` and `white-space: normal` combined with optimized `width` and `min-width` boundaries to ensure the high-density table collapses elegantly and completely eliminates horizontal scrolling on single screens, even with extended `Sector` descriptions and long arrays of `Risks`.

## 3. Mapping Logic Data → UI Classes

To faithfully reconstruct the exact look and feel of the original radar table without hardcoding styles, the generator implements a strict mapping dictionary:

### A. Sector Tag Coloring (`Sector`)
- "PGM · Ti · V · Cu" → `s-pgm`
- "黄金/锑/钨" / "金铀钛" → `s-gold`
- "铜金" / "铜" → `s-copper`
- "铀" → `s-uranium`
- "石墨" → `s-critical`
- "生物能源" → `s-energy`
- "皮肤科" → `s-pharma`

*Fallback logic*: If a sector is unknown, a neutral gray tag class is applied.

### B. Event Pills Formatting (`Catalysts` & `Earnings_Window`)
The script uses regex or keyword matching on the event text to assign background classes:
- Contains "发布", "结果", "季报", "年报" → `e-result` (Blue)
- Contains "钻探", "Drill" → `e-drill` (Green)
- Contains "生产", "首气" → `e-production` (Light Green)
- Contains "融资", "入股", "并购" → `e-corporate` (Purple)
- Contains "重大", "已确认" → `e-hot` (Red/Pink)
- Default / Neutral events → `e-milestone` (Brown)

### C. Six-Month Heatmap (`Heatmap` Array)
The JSON stores each month's status: `{"Month": "Apr", "Status": "Hot"}`.
The build script maps the `Status` string back to CSS height/color bars:
- "Hot" → `<div class="mb mb-hot"></div>` (Deep Red: #B71C1C)
- "Active" → `<div class="mb mb-active"></div>` (Orange: #F57C00)
- "Watch" → `<div class="mb mb-watch"></div>` (Warm Yellow: #FFD54F)

### D. Probability Bar Graph (`Probability`)
The text value determines both the color class and the width of the inline progress bar:
- "极高" (Extremely High) → Width: 95%, Class: `p-vhigh`, Color: #0D47A1
- "高" (High) → Width: 80%, Class: `p-high`, Color: #2E7D32
- "中高" (Medium-High) → Width: 65%, Class: `p-mhigh`, Color: #C0CA33
- "中" (Medium) → Width: 50%, Class: `p-med`, Color: #FBC02D
- "中低" (Medium-Low) → Width: 35%, Class: `p-mlow`, Color: #F57C00
- "低" (Low) → Width: 20%, Class: `p-low`, Color: #D32F2F

## 4. Sorting & Ordering
Since reading a directory yields arbitrary alphabetical order, the script sorts the rows prior to rendering based on a combined breakout key:
1. **Probability Score (Primary):**
   - 极高 (Extremely High) -> -6
   - 高 (High) -> -5
   - 中高 (Medium-High) -> -4
   - 中 (Medium) -> -3
   - 中低 (Medium-Low) -> -2
   - 低 (Low) -> -1
2. **Heatmap Hotness (Secondary):** Evaluates the number of "Hot" months within the 6-month window (More 'Hot' months rank higher in the event of a probability tie).
3. **Alphabetical by Ticker (Tertiary):** Handles any remaining ties.

This combined logical sorting ensures the most explosive stocks (e.g., TM1, DEL) naturally float to the top of the generated HTML table and the breakout ranking panel.

## 5. Development Workflow
1. Update a stock's timeline or catalysts by simply editing the corresponding block in `stocks.yaml`.
2. Run `python generate_radar.py`.
3. The script rewrites `asx_catalyst_radar_6mo.html` instantly.
4. Open the HTML in a browser to see the perfectly formatted, color-coded table.

## 6. JSON Data Schema

The generator strongly expects the root data file `stocks.yaml` to be a YAML list of stock items adhering to the following schema.

```yaml
- Ticker: string             # Required: Stock code (e.g., "TM1")
  "Sector": "string",             // Required: Sector tags (e.g., "PGM · Ti · V · Cu", "铀")
  "Catalysts": [                  // Required: Array of strings, each representing a key catalyst event
    "string"
  ],
  "Risks": [                      // (Optional) Array of strings, each representing a key risk event
    "string"
  ],
  "Earnings_Window": [            // Required: Array of strings for earnings or quarterly report windows
    "string"
  ],
  "Heatmap": [                    // Required: Exactly 6 objects mapping the 6-month radar window
    {
      "Month": "string",          // e.g., "Apr", "May"
      "Status": "string"          // Mapping: "Hot" | "Active" | "Watch" | "Inactive"
    }
  ],
  "CR_Risk": "string",            // Required: Capital raising risk condition (e.g., "高风险", "低 — ...")
  "Probability": "string",        // Required: Breakout probability rating ("极高" | "高" | "中高" | "中" | "低中" | "低")
  "Core_Notes": "string",         // Required: Detailed string; Supports \n for explicit linebreaks and ⚠ for inline warning badge formatting
  "Timeline_Title": "string",     // (Optional) Specific header text for the timeline section (if Timeline is provided)
  Timeline:
    - Time: string           # Time label (e.g., "2026年1月", "即将到来")
      Event: string          # Event description
```
