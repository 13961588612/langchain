# 06 Agent 后端对接

IntentGate 通过 `AgentBackend` 抽象对接智能体，**Agent 不感知 IM 通道**。

---

## 1. 接口定义

```python
class AgentBackend(ABC):
    async def chat(
        self, message: StandardMessage
    ) -> AsyncIterator[AgentReply]:
        """用户文本 → 流式 AgentReply"""

    async def handle_action(
        self, event: CardActionEvent
    ) -> AsyncIterator[AgentReply]:
        """复杂卡片动作（慢路径）→ 流式 AgentReply"""
```

工厂：`intentgate/adapters/__init__.py` → `create_agent_backend(settings)`

| 配置值 | 实现类 |
|--------|--------|
| `mock` | MockAgentBackend |
| `agentscope` | AgentScopeBackend |
| `aethermind` | AetherMindBackend |

---

## 2. AgentScope（主后端，当前重点）

### 2.1 定位

[AgentScope](https://github.com/agentscope-ai/agentscope) 是阿里通义实验室开源的企业级智能体框架（ReActAgent、Toolkit、MsgHub、MCP、A2A 等）。IntentGate **不嵌入** AgentScope，而是通过 HTTP/SSE 调用独立部署的 AgentScope Bridge 服务。

```
IntentGate ──HTTP/SSE──► AgentScope Bridge ──► ReActAgent + Toolkit
                                                    └──► MCP / 业务 API
```

### 2.2 不适用协议说明

| 协议 | 用途 | 是否用于 IntentGate |
|------|------|---------------------|
| **ACP**（Agent Client Protocol） | IDE ↔ 编码 Agent | ❌ 场景不匹配 |
| **A2A**（Agent-to-Agent） | Agent 间互操作 | ⚠️ Agent 内部编排，非 Gateway 协议 |
| **MCP** | 工具调用 | ✅ Agent 内部使用 |
| **Agent API**（Runtime） | 流式对话 SSE | ✅ Bridge 可参考 |

### 2.3 Bridge 服务职责

独立进程（建议端口 8100），提供：

```
POST /v1/sessions/{session_id}/messages   → SSE AgentReply
POST /v1/sessions/{session_id}/actions    → SSE AgentReply
```

Bridge 内部：

1. 维护 `session_id` → AgentScope 对话上下文
2. `StandardMessage.text` → `Msg(role=user)` → `ReActAgent`
3. 流式文本 → `AgentReply(kind=stream)`
4. 工具 `show_card` 返回 → `AgentReply(kind=card)`

### 2.4 卡片工具（AgentScope Toolkit）

```python
from agentscope.tool import Toolkit, ToolResponse

def show_card(
    template: str,
    slots: dict,
    task_id: str | None = None,
) -> ToolResponse:
    """展示结构化卡片，由 IntentGate 渲染发送。"""
    return ToolResponse(content=[{
        "type": "card_intent",
        "template": template,
        "slots": slots,
        "task_id": task_id,
    }])

def update_card_hint(task_id: str, message: str) -> ToolResponse:
    """提示 Gateway 更新卡片（可选，多数 update 走快路径）。"""
    return ToolResponse(content=[{
        "type": "card_update_hint",
        "task_id": task_id,
        "message": message,
    }])

toolkit = Toolkit()
toolkit.register_tool_function(show_card)
```

Bridge 解析 `ToolResponse`：

| content.type | 转换 |
|--------------|------|
| `card_intent` | `AgentReply(kind=card, card=CardIntent(...))` |
| 文本 | `AgentReply(kind=text)` 或 stream |

### 2.5 Pipeline 建议

```
用户文本
  → Router（关键词 / 小模型 → 是否卡片场景）
  → Worker Agent（ReAct + 业务 MCP 工具）
  → 需展示结果时调用 show_card(template, slots)
  → Bridge 流式输出 AgentReply
```

审批、工单、告警、待办可规则路由到固定模板，减少通用闲聊占用卡片带宽。

### 2.6 IntentGate 侧配置

```env
AGENT_BACKEND=agentscope
AGENT_BACKEND_URL=http://127.0.0.1:8100
```

`AgentScopeBackend`（`intentgate/adapters/agentscope.py`）消费 SSE，逐行解析 `data: {AgentReply JSON}`。

### 2.7 AgentScope Bridge 最小 SSE 示例

```python
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse

app = FastAPI()

@app.post("/v1/sessions/{session_id}/messages")
async def chat(session_id: str, message: dict):
    async def generate():
        # 1. stream 思考中
        yield {"data": AgentReply(
            session_id=session_id, kind="stream",
            stream=StreamChunk(id="s1", content="正在处理…", finish=False),
        ).model_dump_json()}
        # 2. 跑 agent ...
        # 3. 若工具返回 card_intent
        yield {"data": AgentReply(
            session_id=session_id, kind="card",
            card=CardIntent(template="crm_approve", slots={...}),
        ).model_dump_json()}
    return EventSourceResponse(generate())
```

### 2.8 多 Agent 编排

Gateway **不参与** MsgHub / Pipeline。复杂编排留在 AgentScope 内部：

- 审批 Agent + 查询 Agent 通过 MsgHub 协作
- 对 Gateway 仍表现为单一 `AgentBackend` 端点

---

## 3. AetherMind（后期备选）

### 3.1 定位

AetherMind 是仓库内基于 LangGraph / DeepAgents 的智能体平台（`practice/aethermind/`），提供 Web UI、Agent CRUD、SSE 对话等。

IntentGate 与 AetherMind **平级**：IntentGate 管 IM 通道与卡片，AetherMind 管 Agent 运行时。

### 3.2 对接方式

配置：

```env
AGENT_BACKEND=aethermind
AGENT_BACKEND_URL=http://127.0.0.1:8000
AETHERMIND_AGENT_ID=your-agent-uuid
```

`AetherMindBackend` 调用：

```
POST /api/agents/{agent_id}/chat
POST /api/agents/{agent_id}/actions   # 待 AetherMind 扩展
```

SSE 事件需映射为 `AgentReply`（P4 定义 event type `card_intent`）。

### 3.3 AetherMind 侧改造（P4）

1. **DeepAgents 工具** `show_card`：与 AgentScope 相同 schema
2. **SSE 事件扩展**：除 text delta 外 emit `card_intent`
3. **Web 通道**：前端 Card 组件消费 `WebRenderer` 输出，与 IM 共用模板

### 3.4 双后端共存

同一 IntentGate 实例同时只连 **一个** AgentBackend。多 Agent 路由在 Agent 层完成，不在 Gateway 切换后端。

若需 A/B：部署两套 IntentGate，不同 Bot 指向不同 `AGENT_BACKEND`。

---

## 4. Mock 后端（开发）

`MockAgentBackend`：回显文本，验证 Gateway 协议链路。

```env
AGENT_BACKEND=mock
```

无需启动外部 Agent 服务。

---

## 5. 对接检查清单

### AgentScope（P1）

- [ ] Bridge 服务可独立启动
- [ ] SSE 输出合法 AgentReply JSON
- [ ] `show_card` 工具注册
- [ ] stream finish 后再发 card
- [ ] session_id 上下文连续多轮
- [ ] IntentGate `AGENT_BACKEND=agentscope` 端到端

### AetherMind（P4）

- [ ] chat SSE 映射 AgentReply
- [ ] show_card 工具
- [ ] actions 端点（慢路径）
- [ ] Web Card 组件

---

## 6. 错误与降级

| 情况 | Gateway 行为 |
|------|--------------|
| Agent 5s 无首字节 | 先发 stream「处理中」 |
| Agent 30s 超时 | 文本「服务繁忙，请稍后重试」 |
| Agent 502 | 告警 + 可选 mock 降级 |
| 工具返回非法 card | 日志 + 文本 fallback |

Agent 侧**不应**尝试直接调用企微 API；所有出站经 IntentGate。
