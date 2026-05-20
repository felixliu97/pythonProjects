# Monopoly — Python/Pygame 实现计划 (最终版)

## 项目目标

基于标准大富翁规则，用纯 Python + Pygame 实现一个带图形界面、人机对战、可存档读档的大富翁游戏。

## 技术选型

| 层 | 技术 | 说明 |
|---|---|---|
| 游戏逻辑 | 纯 Python 3 | 面向对象，无任何外部逻辑依赖 |
| 图形 UI | Pygame | 渲染棋盘、玩家棋子、按钮、弹窗 |
| 存档 | JSON | 全状态序列化，tkinter filedialog 弹出文件选择框 |
| 测试 | unittest + pytest | 102 个单元测试，全部通过 |

## 文件结构

```
playground/games/Monopoly/
├── models.py          # 数据层：Player, Space, PropertySpace, Card, Bank
├── board_data.py      # 40格标准地图 + 32张卡片数据
├── engine.py          # 游戏引擎：状态机、规则执行、存档/读档
├── ui_components.py   # UI组件：Button, LogPanel, PlayerCard, Modal
├── board_view.py      # 棋盘绘制器：地图、房子、棋子
├── main.py            # 主入口：Pygame事件循环 + 侧边栏
├── test_monopoly.py   # 102个单元测试
├── monopoly_rules.md  # 完整游戏规则文档
└── monopoly_data_spec.md  # 40格数据与卡片功能表
```

## 架构设计 (MVC)

```
board_data.py → models.py → engine.py
                                ↑
              ui_components.py + board_view.py
                                ↑
                             main.py
```

## 实现的功能

### 核心规则
- ✅ 40 格标准地图，完整地名与价格
- ✅ 街道/铁路/公共事业各自的租金计算逻辑
- ✅ 垄断 (Monopoly) 时租金翻倍
- ✅ 均匀建房规则 (Even Build) 与均匀拆房规则 (Even Sell)
- ✅ 房子→旅馆升级，银行房产库存限制
- ✅ 抵押/解押 (Mortgage / Unmortgage)，解押需多付 10% 利息
- ✅ 监狱机制：被发配/掷双骰出狱/付$50保释/出狱卡
- ✅ 连续三次双骰进监狱
- ✅ 经过起点 (GO) 获得 $200
- ✅ 破产判定 + 资产转移（欠玩家 vs 欠银行两套逻辑）
- ✅ 16张机会卡 + 16张命运卡，效果全部实现
- ✅ AI 贪心策略：自动购地、自动建房、自动抵押还债

### UI 功能
- ✅ 680px 方形棋盘，完整 40 格渲染
- ✅ 四条边各自带颜色标签条
- ✅ 格子文字（竖排格子使用旋转文字）
- ✅ 房子/旅馆小图标显示在颜色条上
- ✅ 所有者颜色圆点标记
- ✅ 玩家棋子（圆形，多人同格时分组显示）
- ✅ 深色侧边栏：玩家信息卡、日志面板、骰子显示
- ✅ 操作按钮：掷骰/购买/跳过/建房/卖房/抵押/保释/存档/读档
- ✅ 模态弹窗（Modal）用于提示与报错

### 存档/读档
- ✅ `💾 Save Game` 按钮弹出系统对话框选择路径
- ✅ `📂 Load Game` 按钮弹出系统对话框选择文件
- ✅ JSON 序列化：玩家状态、房产归属/建筑/抵押、牌堆顺序、银行库存、游戏阶段

## 运行方法

```bash
# 安装依赖
pip install pygame

# 启动游戏
python playground/games/Monopoly/main.py

# 运行单元测试
python -m pytest playground/games/Monopoly/test_monopoly.py -v
```

## 测试覆盖 (102 tests, 100% pass)

| 测试类 | 测试数 | 覆盖内容 |
|---|---|---|
| TestPlayerModel | 12 | 资金、移动、序列化 |
| TestBoardData | 16 | 40格完整性、卡片数量 |
| TestRentCalculation | 13 | 街道/铁路/公共事业/垄断/抵押 |
| TestBuildingMechanics | 11 | 建房、旅馆、均匀规则、出售 |
| TestMortgage | 4 | 抵押/解押/利息 |
| TestJailMechanics | 6 | 入狱/出狱/保释/出狱卡 |
| TestTurnFlow | 8 | 回合推进、双骰、破产跳过 |
| TestTaxSpaces | 2 | 所得税、奢侈税 |
| TestEngineRentPayment | 2 | 引擎级别的租金收取 |
| TestBankruptcy | 3 | 破产判定、资产转移 |
| TestSaveLoad | 8 | 完整存档/读档往返 |
| TestCardEffects | 10 | 所有卡片类型效果 |
| TestAIBehavior | 3 | AI购地、放弃、建房 |

## 后续扩展方向

- [ ] 拍卖机制 (Auction)：玩家跳过购买时，所有人竞价
- [ ] 玩家间交易 (Trade)：可交易地产/现金/出狱卡
- [ ] 多人支持：在 `main.py` 配置 2-8 个玩家
- [ ] 多难度 AI：防守型、进攻型
- [ ] 音效与动画：移动动效、购买音效
