# AetherMind 文档中心

AetherMind 是公司内部使用的**智能体管理开发平台**：创建、配置、调试多智能体，并通过 Web UI 与 IM 通道使用。

**代码仓库路径**：`practice/aethermind/`

---

## 文档索引

| 文档 | 说明 |
|------|------|
| [01-项目规划](./01-项目规划.md) | 定位、用户、路线图、原则与非目标 |
| [02-架构设计](./02-架构设计.md) | 分层架构、模块职责、数据流、与 IntentGate 关系 |
| [03-数据模型与API](./03-数据模型与API.md) | ORM 模型、REST API、SSE 事件格式 |
| [04-智能体运行时](./04-智能体运行时.md) | AgentRuntime、DeepAgents、ModelHub、Checkpoint |
| [05-阶段能力规划](./05-阶段能力规划.md) | Phase 2–9 详细设计（Soul、Model Hub、Workdir、Skills 等） |
| [06-IntentGate集成](./06-IntentGate集成.md) | 多通道卡片交互、AetherMind 作为 Agent 后端 |
| [07-企业加固规划](./07-企业加固规划.md) | 延后批次：多租户、RBAC、HA、CI/CD、合规 |
| [08-实施与运维](./08-实施与运维.md) | 目录结构、Docker 启动、环境变量、交付状态 |

---

## 阅读顺序

**首次了解**：01 → 02 → 08  
**后端开发**：03 → 04  
**功能迭代**：05（按 Phase 查阅）  
**IM 接入**：06  
**企业化部署**：07

---

## 技术栈摘要

| 层级 | 技术 |
|------|------|
| 智能体 | DeepAgents + LangGraph + LangChain |
| 后端 | FastAPI + Pydantic v2 + SQLAlchemy async |
| 数据库 | PostgreSQL + pgvector + Redis |
| 前端 | Next.js 14 + React 18 + Tailwind CSS |
| 通信 | REST + SSE |
| 追踪 | LangSmith |
| 容器 | Docker Compose |

---

## 当前状态

| Phase | 名称 | 状态 |
|-------|------|------|
| 1 | 平台底座 | ✅ 已完成 |
| 2 | 灵魂系统 | ⬜ 待开发 |
| 3 | Model Hub UI | ⬜ 待开发 |
| 4 | 工作目录 | ⬜ 待开发 |
| 5 | Skills 工场 | ⬜ 待开发 |
| 6 | 多智能体编排 | ⬜ 待开发 |
| 7 | 人机协同 | ⬜ 待开发 |
| 8 | 监控追踪 | ⬜ 部分（LangSmith 基础） |
| 9 | 多通道 | ⬜ 通过 IntentGate 对接 |

---

## 版本

| 版本 | 日期 | 说明 |
|------|------|------|
| 0.1.0 | 2026-05-20 | Phase 1 交付 + 完整文档体系 |
