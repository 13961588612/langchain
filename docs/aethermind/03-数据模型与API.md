# 03 数据模型与 API

## 1. 数据库模型

### 1.1 Agent

表名：`agents`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID string(36) | 主键 |
| `name` | string(255) | 名称 |
| `description` | text | 描述 |
| `system_prompt` | text | 基础系统提示词 |
| `model_provider` | string(50) | openai / anthropic / google / azure / ollama |
| `model_name` | string(100) | 如 gpt-4o |
| `model_parameters` | text (JSON) | temperature、max_tokens 等 |
| `api_key_ref` | string | API Key 引用（Phase 3 加密存储） |
| `work_directory` | string(500) | 工作目录路径，默认 `workdirs/{id}` |
| `soul_config` | text | 灵魂配置（Phase 2 可迁到 soul.md） |
| `profile_config` | text | 行为配置 |
| `is_active` | bool | 是否启用 |
| `is_deleted` | bool | 软删除 |
| `created_at` / `updated_at` | datetime | 时间戳 |

关系：一对多 `Conversation`

### 1.2 Conversation

表名：`conversations`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `agent_id` | FK → agents | 所属 Agent |
| `thread_id` | string | LangGraph thread ID |
| `title` | string | 对话标题 |
| `created_at` / `updated_at` | datetime | 时间戳 |

关系：一对多 `Message`

### 1.3 Message

表名：`messages`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `conversation_id` | FK | 所属对话 |
| `role` | string | user / assistant / system / tool |
| `content` | text | 消息正文 |
| `metadata` | JSONB | 工具调用、Token 等扩展 |
| `created_at` | datetime | 时间戳 |

### 1.4 Skill

表名：`skills`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `name` | string | Skill 名称 |
| `version` | string | 版本 |
| `description` | text | 描述 |
| `tags` | JSONB | 标签 |
| `skill_files` | JSONB | 文件清单 |
| `downloads` | int | 安装次数 |
| `rating` | float | 评分（内部版可选） |

Phase 5 启用完整 CRUD 与内部库。

### 1.5 ModelConfig

表名：`model_configs`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `provider` | string | Provider 名 |
| `model_name` | string | 模型名 |
| `api_key_encrypted` | text | 加密 Key |
| `parameters` | JSONB | 默认参数 |
| `cost_per_1k_tokens` | float | 成本参考 |
| `is_active` | bool | 是否可用 |

Phase 3 启用管理 UI。

### 1.6 Channel

表名：`channels`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `name` | string | 通道名称 |
| `type` | string | web / wechat_work / feishu / dingtalk |
| `config` | JSONB | Bot ID、IntentGate 路由等 |
| `agent_id` | FK | 绑定的默认 Agent |
| `is_active` | bool | 是否启用 |

Phase 9 与 IntentGate 配置联动。

---

## 2. REST API

Base URL：`http://{host}:8000`  
OpenAPI：`/docs`

### 2.1 智能体 Agents

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/agents` | 创建 |
| `GET` | `/api/agents` | 列表 `?page=&page_size=&search=&is_active=` |
| `GET` | `/api/agents/{id}` | 详情 |
| `PUT` | `/api/agents/{id}` | 更新 |
| `DELETE` | `/api/agents/{id}` | 软删除 |
| `POST` | `/api/agents/{id}/activate?active=true` | 启停 |

**创建请求示例**：

```json
{
  "name": "客服助手",
  "description": "处理客户咨询",
  "system_prompt": "你是 Acme 公司客服...",
  "model_provider": "openai",
  "model_name": "gpt-4o",
  "model_parameters": "{\"temperature\": 0.7}",
  "soul_config": null,
  "profile_config": null
}
```

### 2.2 对话 Conversations

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/conversations` | 创建 `{"agent_id","title"}` |
| `GET` | `/api/conversations` | 列表 `?agent_id=&page=` |
| `GET` | `/api/conversations/{id}` | 详情 |
| `DELETE` | `/api/conversations/{id}` | 删除及消息 |
| `GET` | `/api/conversations/{id}/messages` | 历史 `?limit=` |
| `POST` | `/api/conversations/{id}/chat` | **SSE 流式对话** |

### 2.3 系统

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 + Token 用量 |

---

## 3. SSE 流式对话

### 3.1 请求

```
POST /api/conversations/{conversation_id}/chat
Content-Type: application/json

{"message": "你好，请介绍一下自己"}
```

### 3.2 响应事件

| event | 说明 | data 结构 |
|-------|------|-----------|
| `token` | LLM 增量文本 | `{"event":"token","content":"你"}` |
| `tool_call` | 开始调用工具 | `{"event":"tool_call","content":"Calling tool: xxx","metadata":{...}}` |
| `tool_result` | 工具返回 | `{"event":"tool_result","content":"Tool result: xxx",...}` |
| `done` | 完成 | `{"event":"done","metadata":{"thread_id","agent_id"}}` |
| `error` | 错误 | `{"event":"error","content":"错误信息"}` |

### 3.3 前端消费

`frontend/src/lib/api.ts` 使用 `fetch` + `ReadableStream` 解析 SSE，逐 token 更新 UI。

### 3.4 IntentGate 扩展事件（Phase 9，规划）

| event | 说明 |
|-------|------|
| `card_intent` | `{"template":"crm_approve","slots":{...},"task_id":"..."}` |

IntentGate `AetherMindBackend` 将 `card_intent` 映射为 `AgentReply(kind=card)`。

---

## 4. 通用响应结构

### 4.1 分页

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

### 4.2 错误（Phase 1 收尾标准化）

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Agent with id 'xxx' not found",
    "request_id": "req_abc123",
    "timestamp": "2026-05-20T10:00:00Z"
  }
}
```

---

## 5. 认证（规划）

| 阶段 | Header | 说明 |
|------|--------|------|
| Level 1 | `X-API-Key: aethermind_key_xxx` | 全局或 per-deployment |
| Level 2 | `Authorization: Bearer {jwt}` | 用户登录 |

未认证请求返回 `401`；无权限返回 `403`。

---

## 6. API 与 ORM 对应关系

```
AgentCreate/Update  →  Agent ORM  →  AgentRuntime 配置 dict
ConversationCreate  →  Conversation  →  thread_id
ChatRequest         →  Message(user) + stream_chat  →  Message(assistant)
```

更新 Agent 后建议调用 `AgentRuntime.clear_agent_cache(agent_id)` 使配置生效（API 层待补全自动调用）。
