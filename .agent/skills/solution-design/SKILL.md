---
name: solution-design
description: 针对软件架构和系统设计的结构化方法、文档模板以及技术标准。
---

# 技术方案设计 Skill (技术类)

用于提案和评估技术方案的标准流程与文档要求。

## 1. 设计生命周期

对于任何架构层面的修改，需按顺序处理以下核心要素：

1. **问题分析 (Problem Analysis)**：明确功能性需求 (FR)、非功能性需求 (NFR) 以及衡量成功的关键指标。
2. **架构蓝图 (Architecture Blueprint)**：系统组件间的高层交互。强制使用 **Mermaid 图表** 进行可视化。
3. **技术选型 (Technology Selection)**：说明数据库、框架和协议选择的合理性（比较同步与异步方案）。
4. **数据建模 (Data Modeling)**：Schema 结构设计、数据流向以及一致性策略。
5. **接口设计 (Interface Design)**：定义 API 契约、集成模式以及契约测试方案。
6. **韧性与安全 (Resilience & Security)**：缓存策略、负载均衡、灾难恢复 (DR) 以及威胁建模。
7. **实施路线图 (Implementation Roadmap)**：阶段性交付计划（从 MVP 到 V1 演进）及风险规避措施。

## 2. 文档规范标准

- **可视化 (Visuals)**：流程图 (Flowchart) 和实体关系图 (ERD) 必须使用 Mermaid 绘制。
- **方案权衡 (Trade-offs)**：必须记录所评估的备选方案，并详细说明最终选定方案的合理依据。
- **架构模式 (Patterns)**：根据场景合理利用成熟的架构模式（如单体、微服务、事件驱动、读写分离 CQRS 等）。

## 3. 评审清单 (Review Checklist)
- [ ] 是否完全满足了功能性需求 (FRs)？
- [ ] 这是否是能够解决问题的最简方案？
- [ ] 是否识别出了系统可能存在的性能瓶颈？
- [ ] 该设计是否具备可测试性 (Testable) 和可观测性 (Observable)？
