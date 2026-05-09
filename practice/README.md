# AetherMind 通用智能体工作平台 - 实践计划

> **当前定位**：公司内部智能体管理开发平台
> **详细设计**: [内部开发平台规划](../docs/internal-platform-plan.md)
> **企业加固**: 延后批次，详见 [企业级架构文档](../docs/aethermind-enterprise-architecture.md)

## 项目概述

AetherMind 是一个**生产级通用智能体工作平台**，允许用户创建、配置、管理多个 AI 智能体，并通过多通道（Web UI、REST API、企业微信、飞书、钉钉）与之交互。每个智能体拥有独立的工作目录（agent.md / memory.md / soul.md / profile.md）、自定义 Skills、自定义 Model，支持智能体间的协作编排。

## 技术栈

| 层级 | 技术选型 |
|------|---------|
| **智能体框架** | DeepAgents + LangGraph + LangChain |
| **后端框架** | FastAPI + Pydantic v2 |
| **数据库** | PostgreSQL（持久化）+ Redis（缓存/消息队列） |
| **向量存储** | pgvector（PostgreSQL 扩展） |
| **前端** | Next.js 14 + React 18 + Tailwind CSS |
| **通信** | REST API + SSE + WebSocket |
| **容器化** | Docker + Docker Compose |
| **追踪** | LangSmith |

---

## 阶段总览（内部平台）

```
Phase 1 ✅      Phase 2        Phase 3        Phase 4
已完成           灵魂系统        模型中心        工作目录
┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐
│平台底座 │ ──► │Soul +  │ ──► │Model   │ ──► │Workdir │
│        │     │Profile │     │Hub     │     │System  │
└────────┘     └────────┘     └────────┘     └────────┘
                                                    │
Phase 8         Phase 7        Phase 6        Phase 5
监控追踪        人机协同        智能体编排       Skills 工场
┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐
│Monitor │ ◄── │HITL    │ ◄── │Orches- │ ◄── │Skills  │
│+Trace  │     │审批    │     │tration │     │Dev     │
└────────┘     └────────┘     └────────┘     └────────┘

Phase 9
多通道网关
┌────────┐
│Channels│
│Gateway │
└────────┘

───────────────────────────────────────
企业加固（延后批次）
───────────────────────────────────────
认证+RABC / CI-CD+测试 / 高可用+灾备
```

---

## 实践阶段一：平台底座 ✅ 已完成

建立一个可运行的最简平台骨架，打通前后端 + 数据库 + 智能体创建的完整链路。

**已完成：**

1. ✅ **项目初始化与工程结构**
2. ✅ **数据模型设计**（Agent / Conversation / Message / Skill / ModelConfig / Channel）
3. ✅ **智能体 CRUD API**（创建/列表/详情/更新/删除/启停）
4. ✅ **智能体运行时核心**（AgentRuntime + DeepAgents + PostgresSaver）
5. ✅ **前端基础页面**（Agent 列表/创建/编辑/对话页 + SSE 流式输出）
6. ✅ **基础监控**（请求日志 + Token 用量统计）

**Phase 1 收尾 TODO：**
- [ ] Alembic 数据库迁移（替代 `Base.metadata.create_all`）
- [ ] 统一错误响应格式（`APIErrorResponse`）
- [ ] 基础 API Key 认证（简单 Header Token）

---

## 实践阶段二：智能体灵魂系统（Soul & Identity）

**目标**：让每个智能体拥有独立人格和行为偏好，而不是一段 system_prompt 文本。

**任务清单：**

1. **Soul 系统**
   - soul.md 格式规范：YAML frontmatter（name / role / persona / tone / style / values / boundaries / quirks）+ Markdown body
   - 内置 6 种 Soul 模板（助手型/导师型/分析师型/创意型/客服型/技术顾问型）
   - System Prompt 组装器：Soul Identity → Behavior Profile → Tools → Base Instructions
   - Agent 创建时选择 Soul 模板，自动生成初始 soul.md

2. **Profile / Behavior 配置**
   - profile.md 格式：response_length / tool_usage / initiative / language / greeting_style
   - Profile 注入 Agent 行为控制

3. **前端 Soul 编辑器**
   - Agent 编辑页新增"灵魂"Tab
   - Soul 模板选择 + 每个字段可视化编辑
   - 实时预览组装后的 system_prompt
   - 前端 YAML frontmatter 校验

---

## 实践阶段三：Model Hub 模型中心

**目标**：统一管理公司所有 LLM 资源，让开发者选模型不关心 Provider 细节。

**任务清单：**

1. **模型管理界面**
   - 前端 Model 配置页：Provider → Model → API Key → 参数
   - 添加/删除/测试 Provider
   - 本地模型自动扫描（Ollama / vLLM）
   - 模型标签："推荐"/"快速"/"推理"/"编程"/"长文本"

2. **智能模型路由（简化版）**
   - 路由策略：fixed / cheapest_first / best_quality / fallback_chain
   - Agent 创建时选择路由策略 → ModelHub 执行

3. **模型配置存储**
   - ModelConfig CRUD API
   - API Key 加密存储
   - 连接测试端点（POST /api/models/{id}/test）

---

## 实践阶段四：工作目录系统

**目标**：每个智能体拥有完整的、可编辑的、版本化的工作目录。

**任务清单：**

1. **工作目录文件结构**
   ```
   workdirs/{agent_id}/
   ├── agent.md       # 智能体定义文档
   ├── soul.md        # 人格与灵魂
   ├── profile.md     # 行为偏好
   ├── memory.md      # 长期记忆快照（自动维护）
   ├── tools.yaml     # 工具声明
   ├── skills/        # 该 Agent 安装的 Skills
   ├── data/          # 智能体私有数据
   └── .versions/     # 版本历史
   ```

2. **前端工作目录 IDE**
   - 左侧文件树 → 右侧编辑区
   - agent.md / soul.md / profile.md 带 YAML frontmatter 语法高亮 + 实时校验
   - 版本历史查看 + diff 对比 + 回滚

3. **Memory 系统**
   - Layer 1: 对话上下文（PostgresSaver，已实现）
   - Layer 2: 对话摘要（每 10 轮或 > 4000 tokens 触发 LLM 摘要）
   - Layer 3: 长期记忆（pgvector 向量存储 + 语义检索）
   - 前端 Memory 管理：查看/编辑/删除记忆条目

4. **tools.yaml 实现**
   - YAML 声明式工具配置
   - 工具注册中心：内置工具 + 自定义工具
   - 工具权限控制（允许/禁止列表）

---

## 实践阶段五：Skills 开发工场

**目标**：让 AI 开发团队能够开发、测试、共享内部 Skills。

**任务清单：**

1. **Skill 开发器**
   - 前端 Skill 编辑器（Markdown + Frontmatter 表单）
   - Skill 模板系统（web-search / code-analysis / doc-qa / data-analysis）
   - 资源文件管理（上传 scripts / docs / assets）
   - Skill 校验工具（格式校验 + 兼容性检查）

2. **内部 Skills 库**
   - Skills 浏览与搜索
   - 一键安装到指定 Agent
   - Skill 版本管理

3. **Skills 运行时集成**
   - Skills 与 DeepAgents 的 `skills` 参数集成
   - 渐进式披露：触发条件匹配 → 加载完整内容
   - Skills 热加载（清除 Agent 缓存即生效）

4. **内置 Skills**
   - `web-search`: 网络搜索（Tavily 集成）
   - `code-analysis`: 代码分析
   - `doc-qa`: 文档问答
   - `data-analysis`: 数据分析

---

## 实践阶段六：多智能体编排

**目标**：让开发团队设计 Supervisor 模式多智能体协作。

**任务清单：**

1. **Supervisor 编排模式**
   - 编排配置（YAML 声明式）
   - 任务分发 + 结果聚合
   - Routing rules（正则 → Agent 映射）

2. **编排管理**
   - CRUD API + 前端列表页
   - YAML 导入/导出
   - 编排测试运行

3. **编排执行与监控**
   - SSE 事件流（orchestration_start → dispatch → agent_start → result → aggregate → done）
   - 编排运行历史
   - 执行详情页（每个 Agent 的耗时/Token/输出）

---

## 实践阶段七：Human-in-the-Loop（人机协同）

**目标**：敏感操作需人工审批，确保智能体行为可控。

**任务清单：**

1. **审批配置**
   - Agent 级别配置：write_file / execute_command / delete_file / send_message
   - 审批人 + 超时策略

2. **审批交互**
   - Agent 执行中暂停 → 发送审批请求 → 批准/拒绝/超时
   - 前端实时审批通知 + 审批面板

3. **前端审批界面**
   - 待审批队列
   - 查看上下文 + 批准/拒绝
   - 审批历史

---

## 实践阶段八：监控与追踪

**目标**：开发者调试智能体行为，管理员监控系统健康。

**任务清单：**

1. **LangSmith 追踪增强**
   - 自定义 Span 埋点
   - 追踪搜索/过滤

2. **监控面板**
   - 概览卡片（对话数/活跃 Agent/Token 消耗/错误率）
   - Token 用量趋势图
   - Agent 活跃排行
   - 最近错误列表

3. **日志系统**
   - 结构化日志增强
   - 前端简易日志查看器

---

## 实践阶段九：多通道接入网关（最后做）

**目标**：让智能体能接入企业微信、飞书、钉钉。

**任务清单：**

1. **统一通道网关**
   - BaseChannel 抽象
   - 消息标准化（StandardMessage）

2. **企业微信通道**（配置/Webhook/消息适配）
3. **飞书通道**（配置/事件订阅/卡片消息）
4. **钉钉通道**（配置/签名验证/消息适配）
5. **通道管理页面**（可视化配置 + 健康检查）

---

## 简化认证方案（内部版）

```
Level 1（Phase 1 收尾）: API Key 认证
  → 后端生成固定 API Key
  → Header: X-API-Key: aethermind_key_xxx
  → 仅防未授权访问

Level 2（Phase 2-3 补）: 简易用户系统
  → User 模型: email / password_hash / role / is_active
  → Login → JWT (长期有效)
  → 角色: admin / developer / user
  
Level 3（企业加固批次）: 企业 SSO
  → LDAP / OIDC 集成
```

---

## 企业加固（延后批次）

以下在企业化部署前实施，详见 [企业级架构文档](../docs/aethermind-enterprise-architecture.md)：

- **认证增强**：OAuth2 + JWT + RBAC 完整体系
- **多租户**：Shared DB + RLS 隔离
- **CI/CD**：7 阶段流水线 + Canary 部署
- **测试框架**：完整测试金字塔
- **密钥管理**：Vault 自托管
- **审计日志**：ES + PG 分层存储
- **高可用**：Patroni + Sentinel + 多节点
- **灾备**：全量 + WAL 归档 + 异地备份

---

## 最终能力验证清单

完成内部平台全部 9 个阶段后：

- [x] 独立开发完整的智能体工作平台（AetherMind）
- [ ] 为智能体定制灵魂（Soul）和行为（Profile）
- [ ] 统一管理公司所有 LLM 资源 + 智能路由
- [ ] 智能体工作目录开发 IDE（agent.md + soul.md + profile.md + skills/ + memory/）
- [ ] 开发/测试/共享内部 Skills
- [ ] 设计 Supervisor 模式多智能体编排
- [ ] 配置敏感操作人工审批
- [ ] LangSmith 全链路追踪 + 监控面板
- [ ] 通过企业微信/飞书/钉钉使用智能体
- [ ] 简易用户系统 + 角色管理
