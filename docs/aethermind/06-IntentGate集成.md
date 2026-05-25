# 06 IntentGate 集成

AetherMind 与 IntentGate 分工：**AetherMind 负责 Agent 推理，IntentGate 负责 IM 协议与卡片交互**。

---

## 1. 系统关系

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ 企微/飞书   │ ──► │ IntentGate   │ ──► │ AetherMind  │
│ 钉钉/Web    │     │ Card Runtime │     │ AgentRuntime│
└─────────────┘     └──────────────┘     └─────────────┘
                           │                      │
                     CardIntent              show_card 工具
                     5s 快路径                业务 MCP/API
```

| 职责 | IntentGate | AetherMind |
|------|------------|------------|
| WebSocket 长连接 | ✅ | ❌ |
| template_card 渲染 | ✅ | ❌ |
| 按钮 5s update | ✅ | ❌ |
| LLM 推理 | ❌ | ✅ |
| 工具/MCP/记忆 | ❌ | ✅ |
| Web UI 对话 | ❌（直连） | ✅ |

---

## 2. 协议对接

IntentGate `AetherMindBackend` 配置：

```env
AGENT_BACKEND=aethermind
AGENT_BACKEND_URL=http://127.0.0.1:8000
AETHERMIND_AGENT_ID={agent_uuid}
```

### 2.1 用户消息（慢路径）

IntentGate → AetherMind：

```
POST /api/conversations/{conv_id}/chat
或（规划专用端点）
POST /api/agents/{agent_id}/chat
Body: {"message": "...", "session_id": "wecom:..."}
Accept: text/event-stream
```

AetherMind → IntentGate：SSE 事件映射：

| AetherMind event | IntentGate AgentReply |
|------------------|----------------------|
| token (聚合) | kind=stream |
| card_intent | kind=card |
| 文本完成 | kind=text |
| markdown | kind=markdown |

### 2.2 卡片动作（慢路径）

复杂按钮（非快路径白名单）：

```
POST /api/agents/{agent_id}/actions
Body: CardActionEvent JSON
→ SSE AgentReply 流
```

### 2.3 show_card 工具

AetherMind Agent 工具返回：

```json
{
  "type": "card_intent",
  "template": "crm_approve",
  "slots": {
    "orderNo": "20260520001",
    "orderId": "12345",
    "amount": "9800",
    "shopName": "华东店",
    "applicant": "张三"
  },
  "task_id": "crm:approve:12345:v1"
}
```

Runtime 检测 tool 输出 → yield SSE `event=card_intent`。

IntentGate 用共享 `cards/*.yaml` 模板渲染（模板库可 submodule 或 CI 同步）。

---

## 3. 会话映射

| IntentGate | AetherMind |
|------------|------------|
| `session_id` | 映射到 `Conversation` 或内存 thread |
| `wecom:default:bot1_chat1_2` | 可复用固定 conversation_id per session |

建议 IntentGate Session Store 存：

```json
{
  "session_id": "wecom:...",
  "aethermind_agent_id": "uuid",
  "aethermind_conversation_id": "uuid"
}
```

首次消息时 AetherMind `POST /api/conversations` 创建对话，之后复用。

---

## 4. 流式与卡片分包

企微要求：**stream finish 后再发 card**。

Agent 侧推荐顺序：

1. SSE stream：「正在查询…」
2. stream finish
3. SSE card_intent：查询结果卡片

IntentGate Outbound 负责分成两条企微 `aibot_respond_msg`。

---

## 5. 快路径不经 AetherMind

审批「通过/驳回」等标准按钮：

```
用户点击 → IntentGate EventRouter（快路径）
         → 调 CRM API 落库
         → CardRuntime update 卡片
         （不调用 AetherMind）
```

仅改参数、复杂改单等走 AetherMind 慢路径。

---

## 6. Channel 表配置

AetherMind `channels` 表（Phase 9）：

```json
{
  "name": "企微 CRM _bot",
  "type": "wechat_work",
  "agent_id": "agent-uuid-for-crm",
  "config": {
    "intentgate_url": "http://intentgate:8090",
    "wecom_bot_id": "BOTID"
  },
  "is_active": true
}
```

IntentGate 侧按 bot_id 路由到对应 `AETHERMIND_AGENT_ID`。

---

## 7. Web 通道（共用 CardIntent）

AetherMind 对话页可嵌入 IntentGate `WebRenderer` 输出的 Card 组件：

- 同一 `crm_approve.yaml` 模板
- 点击按钮 → 调 IntentGate `/api/v1/actions` 或 AetherMind actions API

实现 Web 与 IM **卡片 UI 一致**。

---

## 8. 实施顺序

| 步骤 | 负责 | 内容 |
|------|------|------|
| 1 | IntentGate P1 | 企微 WS + AgentScope 先验证 |
| 2 | AetherMind P9 | card_intent SSE + show_card |
| 3 | 联调 | IntentGate `AGENT_BACKEND=aethermind` |
| 4 | 业务 | CRM 快路径 handler + 模板 |

AgentScope 与 AetherMind 可并行对接 IntentGate，**AgentBackend 接口相同**。

---

## 9. 联调检查清单

- [ ] AetherMind SSE 含 card_intent
- [ ] IntentGate 渲染 crm_approve 成功
- [ ] 企微收卡 + 点击 + 5s 内 update（快路径）
- [ ] 复杂动作走 AetherMind 慢路径
- [ ] session 多轮上下文连续
- [ ] stream 与 card 分包正确

IntentGate 协议细节见其文档目录 `docs/intentgate/`（CardIntent、AgentReply 定义）。

---

## 10. 对标 Hermes Gateway 的能力矩阵

AetherMind **不内置** Hermes 式 Gateway；下列能力需明确归属，避免 IM 体验与安全缺口。

| 能力 | Hermes Gateway | IntentGate | AetherMind | 规划 Phase |
|------|----------------|------------|------------|------------|
| IM 连接/回调 | ✅ | ✅ 主责 | ❌ | IntentGate P1 |
| 模板卡片 / 5s update | 部分 | ✅ 主责 | ❌ | IntentGate P1–P2 |
| CardIntent 渲染 | ❌ | ✅ | 产出 `show_card` | AetherMind P9 |
| LLM / 工具 / MCP | ✅ | ❌ | ✅ 主责 | AetherMind P2+ |
| 用户配对 / allowlist | ✅ | ⬜ | 配置 API | IntentGate P2 |
| Slash 命令（/model 等） | ✅ | ⬜ 可选 | Agent 切换 API | IntentGate P3 |
| Session 路由 | ✅ | ✅ | Conversation 映射 | P9 联调 |
| Cron 投递到 IM | ✅ | ⬜ | Scheduler 触发 | AetherMind P8 → IG P9 |
| Gateway Hooks | ✅ | ⬜ 可选 | 审计 webhook | 远期 |
| Web UI 对话 | ❌ | WebRenderer | ✅ 主责 | 已有 |

### 10.1 AetherMind 需提供而 IntentGate 消费的 API

| API | 用途 |
|-----|------|
| `POST /api/agents/{id}/chat` | IM 慢路径对话（SSE） |
| `POST /api/agents/{id}/actions` | 复杂卡片动作 |
| `GET /api/channels/{id}/routing` | bot_id → agent_id 映射 |
| `POST /api/internal/sessions/pairing` | 同步 allowlist（可选） |

### 10.2 Scheduler → IntentGate 投递链

```
AetherMind Scheduler (Phase 8)
    → AgentLoop.run_turn
    → card_intent / text
    → HTTP POST IntentGate /api/v1/proactive（规划）
    → aibot_send_msg
```

IntentGate 侧需新增 **proactive 入站 API**（与 Phase 8 同步规划）。

---

## 11. 联调检查清单（补充）

- [ ] Scheduler 定时任务 → IntentGate 主动推卡片
- [ ] allowlist 未授权用户被拒绝（IntentGate P2）
- [ ] AetherMind Cancel 后 IntentGate 停止 stream 刷新
