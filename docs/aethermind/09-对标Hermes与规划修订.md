# 09 对标 Hermes 与规划修订

> 对标参考：[Hermes Agent](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture)（NousResearch 开源 Agent 运行时 + 内置 Gateway）。  
> 本文档记录差距分析结论，并作为 **2026-05 规划修订** 的权威说明。后续 Phase 排期以修订版为准。

---

## 1. 定位差异（不必照搬 Hermes）

| 维度 | Hermes Agent | AetherMind |
|------|--------------|------------|
| 目标用户 | 个人/小团队、CLI 开发者 | 公司内部开发团队 + 业务用户 |
| 入口 | CLI、Gateway、ACP、Cron | Web UI、API、IntentGate（IM） |
| 通道 | 内置 20+ 平台 Gateway | **IntentGate** 外置（卡片交互更强） |
| 运行时 | 自研 `AIAgent` 单循环 | DeepAgents + LangGraph |
| 编排 | delegate 子 Agent | Supervisor YAML + LangGraph |
| 企业化 | 弱 | 多租户/RBAC 独立批次 |

**结论**：AetherMind 不应复制 Hermes 全栈，但需补齐 Hermes 已验证的 **Agent 平台必备运行时能力**。

---

## 2. 识别的结构性缺口（修订前）

| 优先级 | 缺口 | Hermes 做法 | 原 AetherMind 规划问题 |
|--------|------|-------------|------------------------|
| **P0** | 平台无关 Agent Loop | 单 `AIAgent` 服务多入口 | 仅 Web SSE 一条链，绑死 DeepAgents |
| **P0** | Context 压缩/引擎 | 可插拔 ContextEngine，50% 阈值压缩 | 压缩推到 Phase 4 Memory，过晚 |
| **P0** | Tool Registry + MCP | 70+ 工具、toolsets、MCP 一等公民 | 未规划 Registry，仅 DeepAgents 默认工具 |
| **P0** | 最小 HITL | 危险命令执行前拦截 | HITL 在 Phase 7，Workdir 工具更早 |
| **P1** | Cancel / Queue / Cron | 可中断、定时 Agent 任务 | Redis 未用；无 Scheduler |
| **P1** | Gateway 能力边界 | 配对、Slash、Hooks、Cron 投递 | 全推 IntentGate，边界未写清 |
| **P1** | 会话检索/运维 | SQLite FTS5 会话搜索 | Phase 8 才 Dashboard |
| **P2** | Provider 深度 | 18+ Provider、api_mode、credential pool | 仅 5 Provider + 简单 fallback |
| **P2** | 开发者 CLI | `hermes` CLI | 无 |
| **P2** | 测试 | 数千用例 | 推到企业批次 E2 |

---

## 3. AetherMind 应坚持的优势

1. **IntentGate + CardIntent**：企微 5s 卡片、快/慢路径，优于 Hermes 通用 IM 消息。
2. **Web 管理面**：非技术用户可用，适合内部推广。
3. **LangGraph 编排**：复杂企业流程比 Hermes 单循环更适合。
4. **企业加固路线**：多租户、RLS、审计与 Hermes 定位不同。
5. **双 Agent 栈**：IntentGate 可同时接 AgentScope 与 AetherMind。

---

## 4. 规划修订摘要

### 4.1 新增/调整的核心模块

| 模块 | 路径（规划） | 说明 |
|------|--------------|------|
| **AgentLoop** | `core/agent_loop.py` | 平台无关 `run_turn()` 抽象，DeepAgents 为实现之一 |
| **ContextEngine** | `core/context_engine.py` | 压缩、裁剪、prompt 稳定性 |
| **ToolRegistry** | `core/tool_registry.py` | toolsets、MCP、按 Agent/通道启用 |
| **ToolGuard** | `core/tool_guard.py` | 最小 HITL：危险工具执行前拦截 |
| **TaskQueue** | `core/task_queue.py` | Redis 长任务、Cancel token |
| **Scheduler** | `core/scheduler.py` | Cron 触发 Agent → IntentGate 推送 |

### 4.2 修订后 Phase 路线图

```
Phase 1 ✅  + 1.5 收尾（门禁，必须完成）
    ↓
Phase 2   Soul + Context Engine + Tool Registry（MCP）
    ↓
Phase 3   Model Hub + Cancel/Queue
    ↓
Phase 4   Workdir + ToolGuard（最小 HITL）
    ↓
Phase 5   Skills 内部库
    ↓
Phase 6   编排 + delegate 工具
    ↓
Phase 7   HITL 完整 UI + 审批流
    ↓
Phase 8   监控 + 会话检索 + Scheduler
    ↓
Phase 9   IntentGate 全链路 + Cron 投递 IM
```

### 4.3 Phase 1.5 门禁（Phase 2 前置条件）

- [ ] Alembic 数据库迁移
- [ ] 统一 `APIErrorResponse`
- [ ] `X-API-Key` 认证
- [ ] API + AgentRuntime mock **集成测试**（≥10 用例）

**未完成 1.5 不得启动 Phase 2 功能开发。**

---

## 5. IntentGate vs Hermes Gateway 能力矩阵

| 能力 | Hermes Gateway | IntentGate | AetherMind |
|------|----------------|------------|------------|
| IM 长连接/回调 | ✅ 内置 | ✅ 主责 | ❌ |
| 模板卡片/5s update | 部分 | ✅ 主责 | ❌ |
| CardIntent 渲染 | ❌ | ✅ | 产出 `show_card` |
| 用户配对/allowlist | ✅ | ⬜ P2 规划 | 配置同步 API |
| Slash 命令 | ✅ | ⬜ P3 可选 | Agent 切换 API |
| Session 路由 | ✅ | ✅ | Conversation 映射 |
| Cron 投递到 IM | ✅ | ⬜ Phase 8 | Scheduler 触发 |
| Hooks 生命周期 | ✅ | ⬜ 可选 | 审计 webhook |
| LLM 推理 | ✅（内置） | ❌ | ✅ 主责 |
| MCP/工具 | ✅ | ❌ | ✅ 主责 |

---

## 6. Agent Loop 设计要点（对标 Hermes AIAgent）

```python
class AgentLoopBackend(ABC):
    async def run_turn(
        self,
        ctx: TurnContext,  # agent_id, thread_id, channel, user_id
        message: str,
        *,
        cancel_token: CancelToken | None = None,
    ) -> AsyncIterator[AgentEvent]:
        """统一事件：token | tool_call | tool_result | card_intent | done | error"""

class DeepAgentsBackend(AgentLoopBackend):
    """现有 AgentRuntime 演进为实现类"""
```

**入口统一**：

| 入口 | 调用 |
|------|------|
| Web SSE | `AgentLoop.run_turn` |
| IntentGate Backend | 同上 |
| Scheduler | 同上，`channel=scheduler` |
| 未来 CLI | 同上 |

**设计原则**（采纳 Hermes）：

- **Prompt 稳定性**：对话中不随意改 system prompt（除显式 `/model` 类操作）
- **可中断**：`cancel_token` 取消进行中的 turn
- **可观测**：每 turn 产生 `turn_id` 写日志与 LangSmith

---

## 7. Context Engine 设计要点

| 机制 | 触发 | 实现 |
|------|------|------|
| L1 Checkpointer | 每轮 | PostgresSaver（已有） |
| **压缩** | context > 模型窗口 50% | LLM 摘要中间轮次，保留 system + 最近 N 轮 |
| L2 摘要 | 每 10 轮或 >4000 tokens | 写入 Conversation.summary |
| L3 长期 | 关键事实 | pgvector + memory.md（Phase 4 后期） |
| Prompt Cache | Anthropic 等 | 可选，Phase 3+ |

接口：

```python
class ContextEngine(ABC):
    def before_turn(self, messages: list, model_ctx_limit: int) -> list: ...
    def after_turn(self, messages: list, turn_result: TurnResult) -> None: ...
```

---

## 8. Tool Registry 设计要点

```yaml
# tools.yaml / Agent 级配置
toolsets:
  enabled: [filesystem, mcp, crm]
  disabled: [terminal, browser]
  guard:
    write_file: require_approval
    execute_command: deny  # Phase 4 前默认 deny
```

| Toolset | 工具示例 | 默认 |
|---------|----------|------|
| `filesystem` | read/write/list | 开发 Agent 启用 |
| `mcp` | 动态 MCP 工具 | Phase 2 起 |
| `crm` | 业务 API 封装 | 业务 Agent |
| `card` | show_card | IM Agent |
| `terminal` | execute_command | 默认 **关闭** |
| `delegate` |  spawn_subagent | Phase 6 |

MCP：Phase 2 接入 `langchain-mcp` 或等价客户端，经 Registry 注册。

---

## 9. Scheduler 设计要点

```
Cron Job (AetherMind)
    → AgentLoop.run_turn(prompt, agent_id)
    → 结果 card_intent 或 text
    → IntentGate proactive push（或 Web 通知）
```

| 字段 | 说明 |
|------|------|
| `schedule` | cron 表达式 |
| `agent_id` | 执行 Agent |
| `prompt` | 任务描述 |
| `delivery` | intentgate_session / webhook / none |
| `enabled` | 开关 |

存储：`scheduler_jobs` 表或 Redis + APScheduler。

---

## 10. 修订后风险对照

| 风险 | 原对策 | 修订对策 |
|------|--------|----------|
| Context 爆窗 | Phase 4 Memory | Phase 2 ContextEngine |
| 危险工具 | Phase 7 HITL | Phase 4 ToolGuard + Phase 7 UI |
| IM 超时 | IntentGate 快路径 | 不变 + Scheduler 不经对话 |
| 多入口混乱 | 无 | AgentLoop 抽象 |
| 测试债务 | 企业 E2 | Phase 1.5 起集成测试 |

---

## 11. 明确不做（相对 Hermes）

| Hermes 能力 | AetherMind 决策 |
|-------------|-----------------|
| 内置 20 平台 Gateway | 不做，IntentGate 负责 |
| ACP IDE 集成 | 不做（可选远期） |
| Trajectory 训练数据导出 | 不做 |
| 7 种 Terminal 后端 | Phase 4+ 仅 Docker 沙箱可选 |
| Profile 多实例 CLI | 不做，Web + 租户（企业批次） |

---

## 12. 文档与代码同步清单

修订涉及文档：

- [x] 本文档 `09-对标Hermes与规划修订.md`
- [x] `01-项目规划.md` — 路线图与门禁
- [x] `02-架构设计.md` — AgentLoop、ToolRegistry、ContextEngine
- [x] `05-阶段能力规划.md` — Phase 重排与新增章节
- [x] `06-IntentGate集成.md` — Gateway 能力矩阵
- [x] `04-智能体运行时.md` — 演进为 AgentLoop Backend
- [x] `08-实施与运维.md` — Phase 1.5 门禁

代码实现按修订 Phase 逐步落地，**文档先行**。

---

## 13. 版本

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-05-20 | 初版：Hermes 对标与规划修订 |
