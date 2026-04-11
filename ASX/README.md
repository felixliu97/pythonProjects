# ASX 投研仪表盘与自动化管线 (ASX Research Dashboard & Automation) `v1.2`

一个强大的自动化投研数据管线，用于分析 ASX（澳大利亚证券交易所）股票，主要聚焦于高增长潜力以及基本面催化剂（Catalysts）的追踪。

## 🚀 核心功能 (Key Features)

- **自动化流水线 (Automated Pipeline)**：自动抓取最新的市场公告，分析技术面动能，并生成具备高级质感的 HTML 交互式仪表盘。
- **可视化趋势分析 (Visual Trends)**：仪表盘内置 **SVG Sparklines(迷你走势图)**，直观展示过去 30 个交易日的价格动能轨迹。
- **基本面深度增强 (Fundamental Enrichment)**：自动集成 **市值 (Market Cap)**、**市盈率 (P/E)**、**市销率 (P/S)** 及 **股息收益率 (Yield)** 等核心指标。
- **增量同步与并发抓取 (Performance)**：支持批量下载与高并发基本面拉取，提供“断点续传”模式。

### 📊 核心视图 (Core Views)
*   **📊 Market Trends**: 全市场动能扫描，包含 1D/5D 涨跌、RSI、成交量激增及综合动能评分。
*   **🚀 Catalyst Radar**: 深度基本面追踪，包含个股催化剂、风险点记录、融资风险 (CR Risk) 及季度财报窗口。
*   **📢 News Feed**: 过去 14 天 ASX 公告实时流，集成 AI 生成的摘要与重要度评级。
*   **💰 Capital Placements**: 实时跟踪市场融资动向，涵盖增发 (Placement) 与配售权益 (Entitlement Offer)。

## 🛠️ 快速开始 (Getting Started)

### 1. 环境准备 (Prerequisites)
打开项目根目录下的 `.env` 文件，并填入您的数据库连接凭证和其他必要的 API Token：
```bash
# 请不要将真实的密码提交到代码仓库中
```

### 2. 运行完整流水线 (Full Pipeline Execution)
```bash
python run.py all
```
该命令将按顺序运行各项数据爬虫任务（增量模式），执行技术指标分析，并最终在 `output/asx_dashboard.html` 路径下生成最新的可视化报告。

**注意**：使用 `python run.py all --force` 可以强制忽略增量的断点记录，执行完整的历史数据回溯抓取和更新。


### 3. 人机协作的基础研究更新 (Manual Research Update)
1. **数据导出 (Export)**：`python run.py llm-export --ticker RML`
   - 将会在 `config/` 目录下生成供编辑的 `temp_update.yaml` 文件。
2. **AI 编辑 (Edit)**：将 YAML 文件连同您搜集的相关研报发给您偏好的大语言模型（如 Claude / GPT-4），让其基于最新内容更新催化剂、风险或时间表等条目。
3. **数据导入 (Import)**：`python run.py llm-import`
   - 内置的 **Smart Sync（智能同步）** 引擎会自动分析和比对变更，将数据库中被 LLM 抛弃的旧记录进行软删除（状态退役），并安全激活大模型更新的新条目。

### 4. 数据库管理 (Database Management)
- **Schema 定义**：结构定义由 `scripts/db_models.py` 控制。原始的 SQL DDL 语句保留在 `docs/schema.sql` 供技术参考。
- **自动初始化**：`scripts/db_manager.py` 通过 SQLAlchemy 自动在默认的 `postgres` 数据库中创建对应的 Schema 和表结构，无需手动干预。
- **安全重置**：如果发生意外，可运行 `python scripts/reseed_asx.py` 来完全清空当前的 Schema 并从旧版的 YAML 静态源文件重新填充数据库。

---

## 💡 LLM 工作流典型应用场景 (Use Cases)

本系统在设计上原生隔离了**数据提取(Export)**、**大模型推理(Reasoning)**和**数据库状态同步(Import)**，从而确保大模型在自由编辑内容时不会破坏关系型数据库的约束规则。

### 场景 1：批量检查多个股票的最新动态
**需求：** 生成包含多个股票基本面的概要数据，发给大语言模型（LLM），让其结合近期资讯批量检查是否有更新。
**当前设计如何满足：**
系统允许通过逗号分隔的列表或直接使用 `ALL` 关键字，一次性导出多只或所有股票的标准数据结构。
```bash
python run.py llm-export --ticker "BOT,LOT,RML"
# 或者导出整个数据库的所有股票盘点：
python run.py llm-export --ticker ALL
```
拿到生成的 `config/temp_update.yaml` 文件后，你可以将其作为上下文（Context）连同最近的新闻、网络搜索文章等打包发送给大模型（如 Claude / GPT-4），并附上指令：*“请对比这些 YAML 原生数据以及我提供的新闻，更新这几只股票的核心逻辑（core_notes）、主要催化剂（catalysts）或关键时间线（timeline）。请直接输出更新合并后的 YAML。”* 大模型生成修改完毕的 YAML 后，覆盖本地的 `temp_update.yaml`，最后执行 `python run.py llm-import` 即可完成批量更新的无缝数据库入库。

### 场景 2：个股财报/年报深度研读与解构
**需求：** 阅读完某家公司长达百页的最新财务报告后，针对性地为其补充最新的投资备忘录和时间表节点。
**当前设计如何满足：**
```bash
python run.py llm-export --ticker DXB
```
导出单只股票（如 DXB）的数据后，连同财报原始文字发送给 LLM 进行逻辑梳理。LLM 会在 `timeline` 数组下追加新的里程碑节点。依靠 `scripts/llm_workflow.py` 内部实现的智能 SCD Type 2（慢变维追踪）逻辑，系统在 import 读取时，会自动发现**新增**的项目并为其打上生效时间戳，而对于 LLM 去除的原有废弃信息，系统会自动对其进行“软删除”（置为 `is_active=False`）。这意味着你的面板永远只显示最新视角，但底层数据库保留了每一次你和大模型复盘时的推理逻辑快照。

### 场景 3：随时查看股票的历史技术面与动能演变
**需求：** HTML 仪表盘虽然漂亮，但只展示昨晚收盘的瞬间表现。若我想回源追查过去一个月的技术指标轨迹怎么做？
**当前设计如何满足：**
系统并非只有最新切片。核心历史表 `market_trends` 记录着运行流水线时的每天的精确快照。
当你需要深度挖掘某只股票此前的回踩记录（例如查阅过去两周某一天的 RSI 数据、量价激增 `volume_change` 的幅度）时：
利用任意基础数据库可视化工具（如 DBeaver 或者 PgAdmin）连接您的 Postgres：
```sql
SELECT current_price, score, rsi, volume_change, valid_from 
FROM asx.market_trends 
WHERE symbol = 'BOT' 
ORDER BY valid_from DESC;
```
由于采用了时间戳隔离，每天抓取的 `analyzer` 结果都会完好保留，供您进行跨图表比对分析。

### 场景 4：手动加入一只新潜力股，并建立完整的投资档案
**需求：** 我发现了一只很有潜力的新股票（例如 NEU），我想快速将它纳入正在追踪的 "Growth / Catalyst" 分区下，且不破坏现有历史库。
**当前设计如何满足：**
为了保护现有数据的长效性（SCD Type 2 历史记录），我们单独抽离了安全的添加渠道，完整闭环如下：
1. **基础信息注册**：直接使用独立的脚本来注入公司架构体系：
   ```bash
   python scripts/add_stock.py NEU "Neuren Pharmaceuticals Limited" "Healthcare" --type growth
   ```
2. **导出骨架档案**：刚加进去的股票催化剂大多是空白的，为了让 LLM 来帮助快速建档，只需导出该票的初始结构：
   ```bash
   python run.py llm-export --ticker NEU
   ```
3. **大模型投喂范例 (Prompt 建议)**：将生成的 `config/temp_update.yaml` 与财报、新闻或者研究分析师的 PDF 一并喂给大模型（如 Claude），发出如下具体要求：
   > *"我刚将 NEU 这只股票加入了追踪观察池。请详细研读附件中的近期关键公告。参考你拿到的基础 YAML 模板：请提取核心逻辑至 `Core_Notes`，分析可能的融资风险至 `CR_Risk`。将近期重点逻辑划分为 `Catalysts` 和 `Risks` 数组项。最关键的是，帮我抓取未来的事件窗口并罗列在 `Timeline` 中。请保证严格遵守 YAML 语法结构并输出最终答案。"*
4. **导入激活**：LLM 会交出这份结构清晰的公司画像，将内容粘贴覆盖至临时文件并执行 `python run.py llm-import` 将新认知写入数据库。再次执行 `python run.py all` 即可见最终完全体图表挂载成功。

---

## 📊 数据指标与计算逻辑 (Metric Definitions & Logic)

为了帮助投研决策，仪表盘中包含了一系列经过清洗和计算的量化指标。以下是核心逻辑说明：

### 1. 迷你走势图 (Sparklines)
- **数据源**：从数据库 `market_trends.price_history` 字段读取最近 30 个交易日的收盘价。
- **防止溢出**：系统在每次同步时会自动对历史价格执行 `[-30:]` 切片，仅保留最新 30 天数据，确保数据库存储不会随时间无限膨胀。
- **渲染逻辑**：将价格序列归一化至 100x30 的 SVG 空间。
- **颜色代码**：收盘价 ≥ 30天前起始价时显示 **绿色 (#10b981)**，否则显示 **红色 (#ef4444)**。

### 2. 综合评分 (Proprietary Score)
该指标旨在量化短期动能与技术面健康度，公式如下：
`Score = (Momentum * 0.4) + (Vol_Surge * 0.1) - (Volatility * 0.1) + RSI_Adjustment`
- **RSI 超买惩罚**：若 RSI > 70，扣分 `(RSI - 70) * 0.2`。
- **RSI 超卖奖励**：若 RSI < 30，加分 `(30 - RSI) * 0.3`（视为潜在的底部反转动能）。

### 3. 技术指标 (Technical Metrics)
- **动能 (Mom. %)**：计算 5 个交易日的相对涨跌幅：`((当前价 - 5日前价) / 5日前价) * 100`。
- **波动率 (Volatility)**：计算过去一个月的日收益率标准差，并进行百分比缩放。
- **成交量激增 (Vol Surge)**：对比当日成交量与过去 10 个交易日的移动平均成交量：`((今日量 - 10日均量) / 10日均量) * 100`。

### 4. 基本面清洗 (Fundamental Cleaning)
- **股息率 (Yield)**：自动识别 `yfinance` 返回的原始数据格式。如果是小数（如 0.045）则乘以 100 转换为百分比（4.5%）；如果是整数（如 4.5）则直接保留。
- **市值 (Cap)**：自动将原始数值转换为可读的 `b` (Billion) 或 `m` (Million) 格式。

---

## 📜 技术参考：SQL Schema 数据定义 (Technical Reference)

整个数据库的 schema 创建联机语句已提取并在 `docs/schema.sql` 中统一维护。该文件提供了一种幂等（idempotent）的方式来独立重建数据库底层结构。
**警告 (CAUTION)**：在生产环境中运行该文件里的 `DROP` 段落将**永久删除所有数据**，请谨慎操作。
