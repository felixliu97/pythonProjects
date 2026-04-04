# 全球大宗商品实时监控面板 (Next.js + FastAPI)

本项目展示了 **“契约驱动开发”（Contract-Driven Development）** 模式在专业金融应用中的实践。通过 FastAPI 后端定义商品数据契约，前端自动生成 100% 类型安全的 SDK，并辅以现代金融科技（Fintech）风格的 UI 设计。

---

## 核心特性

- **18 种实时商品监控**: 覆盖贵金属、能源、工业金属及农产品。
- **100% 类型安全**: 前端通过 `openapi-ts` 读取后端契约，自动同步 SDK。
- **专业金融 UI**: 采用现代 **Premium Dark Theme**。
- **多维行情展示**: 显示当前价格、绝对涨跌值（`change_abs`）及涨跌幅（`%`）。
- **动态图标系统**: 集成 `lucide-react`，根据品类自动渲染图标。

---

## 快速启动

### 1. 启动后端 (API 契约源)

```bash
cd commodity_dashboard/backend
# 激活环境并安装依赖
python -m uvicorn main:app --reload
```

### 2. 同步契约 (The Bridge)

一旦后端运行，执行以下命令同步前端 SDK：

```bash
# 在项目根目录下
sh scripts/generate-client.sh
```

### 3. 启动前端 (Fintech Dashboard)

```bash
cd commodity_dashboard/frontend
npm run dev
```

---

## 契约驱动实验：同步全球大宗商品

1. **后端修改**: 修改 `backend/main.py` 中的 `Commodity` 模型。
2. **执行同步**: 运行 `sh scripts/generate-client.sh`。
3. **前端查看**: 访问 `http://localhost:3000`，UI 将自动适配最新数据契约。

---

## 项目结构
- `commodity_dashboard/backend/`: FastAPI 源码，定义了核心契约.
- `commodity_dashboard/frontend/`: Next.js 源码，包含自动生成的 `src/api-client/`。
- `commodity_dashboard/scripts/`: 包含自动化同步脚本。
- `docs/`: 核心开发理念及模式详解 ([契约驱动模式详解](file:///e:/repos/pythonProjects/FullStack/docs/api_first_pattern.md)).

---

> [!IMPORTANT]
> **类型安全验证**:
> 在前端目录下运行 `npx tsc --noEmit`。如果没有错误，说明全栈代码在类型层面上是 100% 同步且安全的。
