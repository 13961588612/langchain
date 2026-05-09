# AetherMind 企业级架构设计

> ⚠️ **状态：延后批次。** 当前优先实现内部开发平台功能，详见 [内部开发平台规划](./internal-platform-plan.md)。
> 本文档中的企业级基础设施（Phase 0）、企业加固（Phase 9-11）在企业化部署前实施。
>
> **设计原则**：安全第一、租户隔离、可观测、可扩展、自托管友好
> **部署目标**：自建服务器机房
> **多租户**：Shared DB + PostgreSQL RLS
> **认证**：自建 OAuth2 + JWT
> **测试**：务实均衡型（60% 单元 / 30% 集成 / 10% E2E）

---

## 目录

1. [总体架构演进路线图](#1-总体架构演进路线图)
2. [企业级基础设施（新增 Phase 0）](#2-企业级基础设施新增-phase-0)
3. [Phase 1 平台底座 — 企业级回填](#3-phase-1-平台底座--企业级回填)
4. [Phase 2 工作目录系统 — 企业级增强](#4-phase-2-工作目录系统--企业级增强)
5. [Phase 3 多通道网关 — 企业级增强](#5-phase-3-多通道网关--企业级增强)
6. [Phase 4 Skills 市场 — 企业级增强](#6-phase-4-skills-市场--企业级增强)
7. [Phase 5 Model Hub — 企业级增强](#7-phase-5-model-hub--企业级增强)
8. [Phase 6 多智能体编排 — 企业级增强](#8-phase-6-多智能体编排--企业级增强)
9. [Phase 7 Human-in-the-Loop — 企业级增强](#9-phase-7-human-in-the-loop--企业级增强)
10. [Phase 8 运维监控 — 企业级增强](#10-phase-8-运维监控--企业级增强)
11. [Phase 9 企业级后台管理](#11-phase-9-企业级后台管理新增)
12. [Phase 10 安全合规加固](#12-phase-10-安全合规加固新增)
13. [Phase 11 高可用与灾备](#13-phase-11-高可用与灾备新增)
14. [非功能需求矩阵](#14-非功能需求矩阵)

---

## 1. 总体架构演进路线图

```
Phase 0 (新)          Phase 1-8 (增强)          Phase 9-11 (新)
┌──────────────┐      ┌──────────────┐          ┌──────────────┐
│ 企业基础设施   │ ──► │ 业务能力增强   │ ──────► │ 企业级运营     │
│               │      │               │          │               │
│ • 多租户+RLS  │      │ • 工作目录系统 │          │ • 后台管理     │
│ • OAuth2+JWT  │      │ • 多通道网关   │          │ • 安全合规     │
│ • RBAC 权限   │      │ • Skills 市场  │          │ • 高可用灾备   │
│ • API 网关    │      │ • Model Hub    │          │ • 性能调优     │
│ • 审计日志    │      │ • 智能体编排   │          │               │
│ • 密钥管理    │      │ • HITL 审批    │          │               │
│ • 测试框架    │      │ • 全链路监控   │          │               │
│ • CI/CD 流水线│      │               │          │               │
└──────────────┘      └──────────────┘          └──────────────┘
```

---

## 2. 企业级基础设施（新增 Phase 0）

### 2.1 多租户架构（Shared DB + RLS）

#### 设计决策
- **选型理由**：自建机房降低运维成本，RLS 在数据库层保证隔离，避免应用层泄漏
- **租户模型**：`Tenant` → `User`（多对多，一个用户可属多个租户）
- **隔离边界**：所有 API 请求必须在 context 中携带 `X-Tenant-ID` header

#### 数据库设计

```
┌──────────────────────────────────────────────────────┐
│                    PostgreSQL                         │
│                                                      │
│  ┌─────────┐   ┌──────────┐   ┌───────────────┐     │
│  │ tenants │   │  users   │   │user_tenants   │     │
│  │─────────│   │──────────│   │───────────────│     │
│  │ id      │◄──│ id       │   │ user_id (FK)  │     │
│  │ name    │   │ email    │   │ tenant_id(FK) │     │
│  │ slug    │   │ password │   │ role          │     │
│  │ status  │   │ mfa      │   │ is_default    │     │
│  │ quota   │   │ status   │   └───────────────┘     │
│  │ config  │   └──────────┘                          │
│  └─────────┘                                         │
│       │ tenant_id (存在于所有业务表)                    │
│       ▼                                              │
│  ┌───────────────────────────────────────────────┐   │
│  │  RLS Policy:                                   │   │
│  │  CREATE POLICY tenant_isolation ON agents      │   │
│  │  USING (tenant_id = current_setting(           │   │
│  │    'app.current_tenant_id')::uuid)             │   │
│  └───────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

#### 租户生命周期
```
创建租户 → 初始化默认管理员 → 配置租户配额 → 激活
    │                                              │
    ▼                                              ▼
试用期(14d)                                     停用/归档
    │                                              │
    ▼                                              ▼
正式启用 ← 超额警告 ← 配额监控                  90天后删除
```

#### 租户级配置隔离
- **LLM API Key**: 每个租户可配置自己的 Provider Key
- **模型配额**: 租户级 Token 消耗上限、QPS 限制
- **智能体数量**: 租户级最大智能体数
- **存储配额**: 工作目录存储上限
- **通道绑定**: 每个租户绑定独立的通道 App（企业微信/飞书/钉钉）

### 2.2 认证授权体系（OAuth2 + JWT）

#### 整体架构

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  Client  │────►│ API Gateway  │────►│  Backend API  │
│          │     │ (Traefik)    │     │  (FastAPI)    │
│  Access  │     │              │     │               │
│  Token   │     │ JWT 验证      │     │ RBAC 鉴权     │
│          │     │ Rate Limit   │     │ Scope 校验     │
└──────────┘     └──────────────┘     └──────────────┘
       │                                        │
       │  Refresh Token                          │ Token Introspection
       ▼                                        ▼
┌──────────────┐                       ┌──────────────┐
│ Auth Service │                       │ Redis Cache   │
│ (FastAPI)    │                       │ (JWT Blacklist│
│              │                       │  + Session)   │
│ /auth/login  │                       └──────────────┘
│ /auth/refresh│
│ /auth/logout │
│ /auth/me     │
└──────────────┘
```

#### Token 体系

| Token | 有效期 | 存储位置 | 用途 |
|-------|--------|---------|------|
| Access Token | 15 min | 客户端内存 | API 请求鉴权 |
| Refresh Token | 7 days | HttpOnly Cookie | 刷新 Access Token |
| API Key | 永久/可撤销 | 数据库加密存储 | 程序化调用 |
| Personal Access Token | 可配置 | 数据库哈希 | CI/CD / 脚本 |

#### RBAC 权限模型

```
平台级角色 (Tenant-Scoped):

  admin ────── 全部权限（管理租户、用户、系统配置）
   │
  developer ── 创建/编辑智能体、Skills、模型配置
   │
  operator ─── 启动/停止/监控智能体，查看日志
   │
  user ─────── 使用已部署的智能体对话

权限域 (Permission Domains):
  • agents:*      — 智能体管理
  • skills:*      — Skills 管理  
  • models:*      — Model 配置
  • channels:*    — 通道管理
  • conversations:* — 对话操作
  • admin:*       — 系统管理
  • billing:*     — 用量与计费

操作级别:
  • :read         — 查看
  • :write        — 创建/编辑
  • :delete       — 删除
  • :manage       — 完整管理（含启停/审批）
```

#### API Key 体系
```
┌─────────────────────────────────────────────┐
│              API Key 生命周期                 │
│                                             │
│  创建 → 激活 → 使用 ──→ 轮换 → 旧 Key 保留   │
│              │                  │           │
│              ▼                  ▼           │
│          权限范围限制        宽限期(48h)      │
│          IP 白名单          自动过期         │
│          限流配置           撤销             │
└─────────────────────────────────────────────┘

Key 格式: ak_<tenant_shortcode>_<random_32chars>
存储: AES-256-GCM 加密，仅保留前 8 字符明文用于展示
```

### 2.3 API 网关层

#### 网关架构（基于 Traefik）

```
                         ┌──────────────┐
                         │   Traefik    │
                         │  API Gateway │
                         │              │
  Internet ──────────────►  :443 (TLS)  │
                         │  :80→:443    │
                         │              │
                         │  Middleware: │
                         │  • JWT Auth  │
                         │  • Rate Limit│
                         │  • IP Filter │
                         │  • CORS      │
                         │  • Circuit   │
                         │    Breaker   │
                         └──────┬───────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
         ┌──────────┐   ┌──────────┐   ┌──────────┐
         │ Backend  │   │ Frontend │   │ Monitor  │
         │ :8000    │   │ :3000    │   │ :9090    │
         └──────────┘   └──────────┘   └──────────┘
```

#### 限流策略

| 层级 | 维度 | 限制 | 时间窗口 |
|------|------|------|---------|
| 全局 | IP | 300 req | 1 min |
| 租户 | tenant_id | 1000 req | 1 min |
| API Key | key_id | 100 req | 1 min |
| 端点 | /api/agents/{id}/chat | 30 req (per user) | 1 min |
| 端点 | /api/agents (POST) | 10 req (per user) | 1 min |

### 2.4 密钥管理

#### 方案：自建 HashiCorp Vault（或轻量版 Sealed Secrets）

```
┌─────────────────────────────────────────────┐
│            Vault (自托管)                     │
│                                             │
│  Secret Engines:                            │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ │
│  │ kv-v2     │ │ transit   │ │ database  │ │
│  │ (静态密钥) │ │ (加密服务) │ │ (动态凭证) │ │
│  └───────────┘ └───────────┘ └───────────┘ │
│                                             │
│  Auth Methods:                              │
│  ┌───────────┐ ┌───────────┐               │
│  │ AppRole   │ │ JWT/OIDC  │               │
│  │ (服务间)   │ │ (人工访问) │               │
│  └───────────┘ └───────────┘               │
└─────────────────────────────────────────────┘

分层存储：
  Level 1: Vault (Provider Keys / DB 密码 / JWT Secret)
  Level 2: DB 加密列 (租户 API Key / Webhook Secret)
  Level 3: 环境变量 (非敏感配置项，通过 config.py 加载)
```

### 2.5 审计日志

```
审计事件模型：
  {
    "event_id": "uuid",
    "timestamp": "2026-05-09T10:30:00Z",
    "tenant_id": "uuid",
    "actor": {
      "user_id": "uuid",
      "type": "user|api_key|system"
    },
    "action": "agent.create|agent.delete|agent.chat|skill.install|...",
    "resource": {
      "type": "agent|skill|model|channel|conversation",
      "id": "uuid",
      "name": "human-readable"
    },
    "context": {
      "ip": "192.168.1.1",
      "user_agent": "...",
      "channel": "web|api|wechat|feishu"
    },
    "result": "success|failure|denied",
    "detail": "Human-readable description",
    "changes": {"field": {"old": "...", "new": "..."}}
  }

存储策略：
  • 热数据: Elasticsearch (近 90 天，快速检索)
  • 温数据: PostgreSQL (90 天 - 1 年)
  • 冷数据: 压缩归档文件 (> 1 年)
```

### 2.6 测试框架

#### 测试金字塔

```
           ┌─────┐
           │ E2E │  10%  Playwright（关键用户路径）
           └─────┘
        ┌───────────┐
        │ Integration│  30%  pytest + httpx + testcontainers
        └───────────┘
     ┌─────────────────┐
     │   Unit Tests     │  60%  pytest + pytest-asyncio
     └─────────────────┘
```

#### 测试目录结构
```
backend/
├── tests/
│   ├── conftest.py                   # 全局 fixtures
│   ├── unit/
│   │   ├── test_agent_runtime.py     # AgentRuntime 单元测试
│   │   ├── test_model_hub.py         # ModelHub 单元测试
│   │   ├── test_rbac.py              # RBAC 权限逻辑测试
│   │   └── test_config.py            # 配置加载测试
│   ├── integration/
│   │   ├── test_api_agents.py        # Agent API 集成测试
│   │   ├── test_api_conversations.py # 对话 API 集成测试
│   │   ├── test_auth_flow.py         # 认证流程集成测试
│   │   ├── test_tenant_isolation.py  # 租户隔离安全测试
│   │   ├── test_channel_webhook.py   # 通道 Webhook 集成测试
│   │   └── test_skill_market.py      # Skills 市场集成测试
│   ├── e2e/
│   │   ├── test_user_journey.py      # 用户完整旅程
│   │   └── test_multi_agent_orchestration.py
│   └── fixtures/
│       ├── agents.json               # 测试用 Agent 数据
│       ├── tenants.json              # 测试用 Tenant 数据
│       └── mock_llm_responses.py     # Mock LLM 响应
```

#### 测试基础设施
- **testcontainers-python**: 自动启动 PostgreSQL + Redis 容器
- **pytest-asyncio**: 异步测试支持
- **respx / VCR.py**: HTTP 请求录制回放（Mock 外部 LLM API）
- **pytest-cov**: 覆盖率报告（目标：整体 > 75%，核心模块 > 90%）
- **Schemathesis**: 基于 OpenAPI Schema 的自动模糊测试

### 2.7 CI/CD 流水线

#### 流水线架构（基于 GitLab CI 自托管 Runner）

```
Git Push
   │
   ▼
┌──────────────────────────────────────────────────┐
│ Stage 1: Lint & Type Check (2 min)               │
│  • ruff format --check                           │
│  • ruff check                                    │
│  • mypy                                          │
│  • eslint + prettier (Frontend)                  │
│  • Markdown lint                                 │
└──────────┬───────────────────────────────────────┘
           ▼
┌──────────────────────────────────────────────────┐
│ Stage 2: Unit Tests (3 min)                      │
│  • pytest tests/unit/ (并行)                      │
│  • 覆盖率上传                                     │
└──────────┬───────────────────────────────────────┘
           ▼
┌──────────────────────────────────────────────────┐
│ Stage 3: Integration Tests (5 min)               │
│  • docker-compose up (test services)              │
│  • pytest tests/integration/                     │
│  • 租户隔离安全测试                               │
│  • API Schema 兼容性检查                          │
└──────────┬───────────────────────────────────────┘
           ▼
┌──────────────────────────────────────────────────┐
│ Stage 4: Security Scan (3 min)                   │
│  • Trivy 容器镜像扫描                             │
│  • Bandit Python 安全分析                         │
│  • npm audit (Frontend)                          │
│  • 密钥泄露检测 (trufflehog)                      │
└──────────┬───────────────────────────────────────┘
           ▼
┌──────────────────────────────────────────────────┐
│ Stage 5: Build & Package (2 min)                 │
│  • docker build (multi-stage, cache optimized)   │
│  • docker tag + push to private registry         │
│  • Helm chart package                            │
└──────────┬───────────────────────────────────────┘
           ▼
┌──────────────────────────────────────────────────┐
│ Stage 6: Deploy to Staging (auto)                │
│  • helm upgrade (staging namespace)               │
│  • 数据库迁移 (alembic upgrade head)              │
│  • 冒烟测试 (关键 API 健康检查)                    │
└──────────┬───────────────────────────────────────┘
           ▼
┌──────────────────────────────────────────────────┐
│ Stage 7: Deploy to Production (manual trigger)   │
│  • helm upgrade (production namespace)            │
│  • Canary deployment (10% → 50% → 100%)          │
│  • 数据库迁移 (alembic upgrade head)              │
│  • 部署后监控 (5 min 观察窗口)                     │
└──────────────────────────────────────────────────┘
```

---

## 3. Phase 1 平台底座 — 企业级回填

在进入 Phase 2 之前，需要对已完成的 Phase 1 进行企业级加固：

### 3.1 数据库迁移（Alembic）

```
当前问题：
  Base.metadata.create_all() 仅适用于开发环境
  生产环境需要可审计、可回滚的数据库变更管理

引入 Alembic：
  backend/
  ├── alembic/
  │   ├── env.py                    # 迁移环境配置
  │   ├── versions/
  │   │   ├── 001_initial_schema.py # Phase 1 所有模型
  │   │   └── 002_add_tenant.py     # Phase 0 新增租户字段
  │   └── script.py.mako
  └── alembic.ini

迁移策略：
  • 生产环境：alembic upgrade head（CI/CD 自动执行）
  • 回滚：alembic downgrade -1（需审批）
  • 迁移检查：alembic check（CI 阶段自动校验，防止迁移冲突）
```

### 3.2 数据库连接池优化

```
当前配置：
  pool_size=20, max_overflow=10  (hardset)

企业级改进：
  • pool_size: 环境变量 DB_POOL_SIZE (默认 20)
  • max_overflow: DB_POOL_OVERFLOW (默认 10)
  • pool_recycle: 3600 秒（防止连接被 pg 服务端断开）
  • pool_timeout: 30 秒
  • 连接池指标导出到 Prometheus (active/idle/overflow/wait)
  • 慢查询日志（> 500ms）
```

### 3.3 错误处理标准化

```python
# 统一的错误响应格式
class APIErrorResponse:
    error: {
        "code": "RESOURCE_NOT_FOUND",
        "message": "Agent with id 'xxx' not found",
        "request_id": "req_abc123",    # 用于日志关联
        "timestamp": "2026-05-09T..."
    }

# 错误码体系
┌──────────────────────┬────────────────────────────┐
│ HTTP 4xx             │ HTTP 5xx                    │
├──────────────────────┼────────────────────────────┤
│ VALIDATION_ERROR     │ INTERNAL_ERROR              │
│ AUTHENTICATION_ERROR │ SERVICE_UNAVAILABLE         │
│ AUTHORIZATION_ERROR  │ UPSTREAM_ERROR              │
│ RESOURCE_NOT_FOUND   │ LLM_PROVIDER_ERROR          │
│ CONFLICT             │ LLM_TIMEOUT                 │
│ RATE_LIMIT_EXCEEDED  │ LLM_TOKEN_EXHAUSTED         │
│ QUOTA_EXCEEDED       │ DEPENDENCY_ERROR            │
│ TENANT_SUSPENDED     │                             │
└──────────────────────┴────────────────────────────┘
```

### 3.4 健康检查增强

```
当前: GET /api/health → {"status": "ok"}
企业级: GET /api/health → 包含各依赖状态

{
  "status": "healthy|degraded|unhealthy",
  "version": "0.1.0",
  "uptime_seconds": 3600,
  "checks": {
    "database": {"status": "up", "latency_ms": 2},
    "redis": {"status": "up", "latency_ms": 1},
    "vault": {"status": "up"},
    "llm_openai": {"status": "up", "latency_ms": 200},
    "llm_anthropic": {"status": "down", "error": "timeout"},
    "disk_space": {"status": "up", "free_gb": 50}
  }
}

新增端点：
  GET /api/health/live   →  Kubernetes liveness probe
  GET /api/health/ready  →  Kubernetes readiness probe
  GET /api/health/startup → Kubernetes startup probe
```

---

## 4. Phase 2 工作目录系统 — 企业级增强

### 4.1 工作目录存储后端（抽象）

当前仅支持本地 `FilesystemBackend`。企业级需支持多种后端：

```
                      ┌──────────────────┐
                      │  WorkdirManager  │
                      │   (抽象层)        │
                      └────────┬─────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │ Local FS     │   │ MinIO/S3     │   │ Git-backed   │
   │ (默认)       │   │ (共享存储)    │   │ (版本控制)    │
   └──────────────┘   └──────────────┘   └──────────────┘

  自建机房推荐：
    开发/单机: Local FS
    生产/多节点: MinIO (S3-compatible, 自托管)
```

### 4.2 工作目录版本控制

```
workdirs/{agent_id}/
├── agent.md              # 当前版本
├── soul.md
├── profile.md
├── .versions/            # 版本历史
│   ├── agent.md.v1       # 通过 Git-like diff 存储
│   ├── agent.md.v2
│   └── manifest.json     # 版本索引
├── skills/
└── data/

前端功能：
  • 文件历史查看（diff 对比）
  • 版本回滚
  • 版本注释（为什么修改）
  • 版本发布（标记稳定版）
```

### 4.3 多租户工作目录隔离

```
workdirs/
├── {tenant_id}/
│   ├── {agent_id}/
│   │   ├── agent.md
│   │   ├── soul.md
│   │   ├── profile.md
│   │   ├── tools.yaml
│   │   ├── skills/
│   │   └── data/
│   └── ...
└── _shared/               # 跨租户共享（需审批）
    └── templates/         # Agent 模板 / Soul 模板
```

### 4.4 Memory 系统增强

```
Memory 分层架构：

┌──────────────────────────────────────────────┐
│  Layer 1: 短期记忆 (Conversation Context)      │
│  • LangGraph Checkpoint (PostgresSaver)       │
│  • 当前对话窗口（最近 N 条消息）                │
│  • trim_messages 智能裁剪                      │
└──────────────────────────────────────────────┘
              │ 对话结束
              ▼
┌──────────────────────────────────────────────┐
│  Layer 2: 中期记忆 (Session Summary)           │
│  • LLM 自动摘要 (每 N 轮或 token 达到阈值)      │
│  • 存储在 Message 表的 summary 字段            │
│  • 下次对话自动注入                            │
└──────────────────────────────────────────────┘
              │ 定期归档
              ▼
┌──────────────────────────────────────────────┐
│  Layer 3: 长期记忆 (Vectorized Memory)         │
│  • LangGraph Store (Postgres + pgvector)      │
│  • 关键信息向量化存储                          │
│  • 按相关性检索注入当前对话                     │
│  • memory.md 作为记忆摘要的持久化快照           │
└──────────────────────────────────────────────┘

Memory 质量控制：
  • 记忆去重（相似度 > 0.95 视为重复）
  • 记忆衰减（旧记忆降低检索权重）
  • 用户可标记"重要记忆"/"忘记这条"
```

---

## 5. Phase 3 多通道网关 — 企业级增强

### 5.1 通道网关架构

```
                         ┌──────────────────────┐
                         │   Channel Gateway     │
                         │   (FastAPI Router)    │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
       ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
       │ Web Channel  │    │ IM Channels  │    │ API Channel  │
       │              │    │              │    │              │
       │ • SSE  (内置) │    │ • 企业微信    │    │ • REST API   │
       │ • WebSocket  │    │ • 飞书       │    │ • Webhook    │
       └──────────────┘    │ • 钉钉       │    │ • GraphQL    │
                           └──────────────┘    └──────────────┘
                                    │
                           ┌────────┴────────┐
                           │ 消息标准化层      │
                           │ StandardMessage  │
                           └────────┬────────┘
                                    ▼
                           ┌────────────────┐
                           │ Message Router │
                           │ (路由到 Agent)  │
                           └────────────────┘
```

### 5.2 消息队列集成（新增）

当前所有对话是同步的。企业级需要异步任务处理：

```
场景：
  • 长时间运行的 Agent 任务（> 30 秒）
  • 批量消息处理
  • 通道消息重试

架构：
  FastAPI Request
      │
      ▼
  /api/agents/{id}/chat
      │
      ├── 短任务 (< 30s): SSE 直接流式返回（当前方式）
      │
      └── 长任务 (> 30s): ──► Redis Queue (rq / arq)
                                   │
                                   ▼
                              Worker 执行 Agent
                                   │
                                   ▼
                              结果回调 (WebSocket/Webhook通知)
```

### 5.3 通道层安全增强

```
每条通道独立的安全配置：
  • 签名验证 (HMAC-SHA256) → 必须
  • IP 白名单 → 推荐
  • Request 重放防护 (nonce + timestamp)
  • 消息体大小限制 (默认 500KB)
  • 敏感词过滤 (租户可配置敏感词列表)
  • 通道级限流 (独立于全局限流)
  • 通道传输加密 (TLS termination at Traefik)

企业微信特有：
  • 消息加解密 (EncodingAESKey)
  • XML 消息解析 + XML 注入防护

飞书特有：
  • 事件订阅 URL 验证
  • 飞书卡片消息安全校验

钉钉特有：
  • 签名验证 (timestamp + appSecret)
  • Outgoing 机器人回调验证
```

### 5.4 通道健康监控

```
Channel Health Dashboard:
  • 每通道: 在线状态 / 延迟 / 错误率 / 消息吞吐量
  • 告警: 通道离线 > 1 min → 通知管理员
  • 自动切换: 主通道故障 → 降级到备用通道
  • Webhook 日志: 原始请求/响应记录 (可检索、可重放)

GET /api/channels/{id}/health
{
  "status": "healthy|degraded|down",
  "last_heartbeat": "2026-05-09T10:30:00Z",
  "messages_last_hour": 150,
  "error_rate": 0.02,
  "avg_latency_ms": 350
}
```

---

## 6. Phase 4 Skills 市场 — 企业级增强

### 6.1 Skills 安全沙箱（核心安全需求）

企业级 Skills 系统的关键问题是**代码执行安全**。Skills 可能包含 Python/JS 脚本：

```
Skills 执行安全分层：

┌──────────────────────────────────────────────┐
│ Layer 1: 静态分析 (安装前)                      │
│  • SKILL.md 格式校验                           │
│  • allowed-tools 白名单校验                     │
│  • 脚本内容 AST 分析 (禁止 import os/subprocess)│
│  • 文件大小限制                                 │
└──────────────────────────────────────────────┘
              │ 通过
              ▼
┌──────────────────────────────────────────────┐
│ Layer 2: 签名验证                              │
│  • 官方 Skills: DeepAgents 团队签名             │
│  • 社区 Skills: 作者签名 + 社区审核              │
│  • 私有 Skills: 租户管理员签名                   │
│  • 未签名 Skills: 仅沙箱模式运行                 │
└──────────────────────────────────────────────┘
              │ 
              ▼
┌──────────────────────────────────────────────┐
│ Layer 3: 运行时沙箱                             │
│  • 默认: DeepAgents FilesystemBackend          │
│    (仅访问工作目录)                              │
│  • 增强: Deno Sandbox (JS 子进程隔离)           │
│  • 生产: gVisor / Firecracker 微虚拟机          │
│  • 资源限制: CPU/内存/网络/磁盘配额               │
└──────────────────────────────────────────────┘
```

### 6.2 Skills 市场治理

```
Skills 生命周期:
  Draft → Review → Published → Deprecated → Removed

审核流程:
  新 Skill 提交 → 自动检查 → 人工审核 → 上架
                           │
                     ┌─────┴─────┐
                     ▼           ▼
                 安全审核    质量审核
                 (沙箱测试)  (文档/兼容性)

分级体系:
  • Official: 官方维护，完整测试
  • Verified: 社区贡献，经过审核
  • Community: 社区发布，仅自动检查
  • Private: 租户内部使用

评分与反馈:
  • 用户评分 (1-5)
  • 使用统计 (安装数/活跃数)
  • 问题追踪 (GitHub Issues 集成)
```

### 6.3 Skills 跨租户共享

```
┌─────────────────────────────────────────────┐
│            Global Skills Market              │
│  (所有租户可见，需审核上架)                      │
└──────────────┬──────────────────────────────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
┌───────────┐    ┌───────────┐
│ Tenant A  │    │ Tenant B  │
│ Skills    │    │ Skills    │
│ (私有)     │    │ (私有)     │
└───────────┘    └───────────┘

共享机制:
  • 发布到 Global Market: 租户管理员手动提交
  • 跨租户协作: 受邀合作编辑
  • Fork: 基于公开 Skill 创建私有修改版
```

---

## 7. Phase 5 Model Hub — 企业级增强

### 7.1 模型路由策略增强

```
智能路由规则树:

                    ┌─────────────┐
                    │ 用户消息      │
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │ 任务分类器    │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   简单问答            复杂推理            代码/工具
        │                  │                  │
        ▼                  ▼                  ▼
   便宜模型            强大模型           特定模型
  (gpt-4o-mini)      (claude-opus)    (deepseek-coder)
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ 成本超限?    │
                    │ Fallback链  │
                    └─────────────┘

Fallback 链配置 (per tenant):
  gpt-4o → claude-sonnet → gpt-4o-mini → deepseek-v3 → ollama-local
```

### 7.2 自托管模型管理（自建机房重点）

```
本地模型基础设施:

┌──────────────────────────────────────────────┐
│           Model Serving Layer                 │
│                                              │
│  ┌────────────┐  ┌────────────┐              │
│  │ vLLM       │  │ Ollama     │              │
│  │ (生产级)    │  │ (开发/轻量) │              │
│  │            │  │            │              │
│  │ GPU 0/1/2  │  │ GPU 3      │              │
│  │ qwen-72b   │  │ llama-8b   │              │
│  │ deepseek   │  │ codellama  │              │
│  └────────────┘  └────────────┘              │
│                                              │
│  模型加载策略:                                  │
│  • 常驻热模型: 常用模型始终加载                   │
│  • 按需冷启动: 长尾模型闲置 > 30min 卸载           │
│  • LoRA 适配器: 轻量微调不改变基座模型             │
└──────────────────────────────────────────────┘

本地模型注册:
  POST /api/models/local/scan
  → 扫描 vLLM/Ollama 端点
  → 自动注册可用模型列表
  → 显示 GPU 显存占用 / 吞吐量

模型性能基准:
  • 自动化基准测试 (tokens/s / TTFT / latency p50/p99)
  • 并发性能测试 (N 并发下的吞吐量)
  • 模型对比矩阵 (质量 vs 速度 vs 成本)
```

### 7.3 Token 用量与计费（租户级）

```
用量跟踪体系:

┌─────────────────────────────────────────────┐
│          Token Usage Tracker                 │
│                                             │
│  维度:                                       │
│  • tenant_id → 租户总用量                     │
│  • agent_id  → 智能体用量                     │
│  • model     → 按模型分别统计                  │
│  • user_id   → 用户用量                       │
│  • time      → 时/日/周/月 聚合                │
│                                             │
│  限制:                                       │
│  • 软限制: 80% 用尽 → 告警通知                 │
│  • 硬限制: 100% 用尽 → 拒绝新请求               │
│  • 按模型限制: gpt-4o 更严, gpt-4o-mini 更松   │
│                                             │
│  存储:                                       │
│  • 实时: Redis (滑动窗口, 精确计数)            │
│  • 历史: PostgreSQL (聚合后)                  │
│  • 分析: TimescaleDB (时序分析)               │
└─────────────────────────────────────────────┘
```

---

## 8. Phase 6 多智能体编排 — 企业级增强

### 8.1 编排定义（声明式 YAML）

```
编排配置格式 (Orchestration as Code):

# orchestration/team-support.yaml
name: "Customer Support Team"
version: "1.0"
orchestration_mode: supervisor  # supervisor|swarm|map-reduce|pipeline

supervisor:
  agent: "supervisor-agent"
  model: "claude-sonnet"
  routing_rules:
    - pattern: "billing|payment|refund"
      target: "billing-agent"
    - pattern: "technical|bug|error"
      target: "technical-agent"
    - pattern: ".*"
      target: "general-agent"

members:
  - name: "billing-agent"
    model: "gpt-4o"
    tools: [stripe_api, order_lookup]
    skills: [invoice-qa]
    
  - name: "technical-agent"
    model: "claude-sonnet"
    tools: [github_api, log_analyzer]
    skills: [code-analysis, debugging]
    
  - name: "general-agent"
    model: "gpt-4o-mini"
    skills: [knowledge-base-qa]

shared_memory:
  enabled: true
  namespace: "support_team"
  ttl: 86400  # 24h

interrupt_on:
  - action: "refund"
    condition: "amount > 100"
  - action: "delete_data"
```

### 8.2 编排引擎

```
Orchestration Engine 架构:

┌──────────────────────────────────────────────┐
│        OrchestrationRegistry                  │
│  (编排注册中心: 存储/发现/版本管理)              │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│        OrchestrationBuilder                   │
│  (编排构建器: YAML → LangGraph StateGraph)      │
│                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │Supervisor│ │  Swarm   │ │Map-Reduce│ ...  │
│  │ Builder  │ │ Builder  │ │ Builder  │     │
│  └──────────┘ └──────────┘ └──────────┘     │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│        OrchestrationRuntime                   │
│  (编排运行时: 执行/监控/中断/恢复)               │
│                                              │
│  • 并行执行子 Agent                            │
│  • 超时控制 (per-agent timeout)               │
│  • 错误处理 (retry / fallback / escalate)     │
│  • 全局状态追踪 (Orchestration State)          │
│  • 实时事件流 (SSE + WebSocket)               │
└──────────────────────────────────────────────┘
```

### 8.3 编排可视化

```
前端编排编辑器 (React Flow / XYFlow):

┌─────────────────────────────────────────────┐
│  Navigation: [Orchestrations] [Runs]         │
├─────────────────────────────────────────────┤
│                                             │
│   ┌──────────┐                              │
│   │Supervisor│──── conditional edge          │
│   └────┬─────┘                              │
│        │                                     │
│   ┌────┴────┐  ┌─────────────┐              │
│   │Routing  │──│Pattern Match│              │
│   └────┬────┘  └─────────────┘              │
│        │                                     │
│   ┌────┴────────────┐                       │
│   ▼                 ▼                        │
│ ┌──────┐      ┌──────────┐                  │
│ │Agent1│      │  Agent2  │                  │
│ └──┬───┘      └────┬─────┘                  │
│    │                │                        │
│    └───────┬────────┘                        │
│            ▼                                 │
│      ┌──────────┐                           │
│      │Aggregator│                           │
│      └──────────┘                           │
│                                             │
└─────────────────────────────────────────────┘

  节点属性面板:
  • Agent 选择
  • Model 选择
  • 提示词模板
  • 超时设置
  • 重试策略
  • 输出映射 (output → next agent input)

  编排监控 (运行时):
  • 节点高亮 (executing/success/error)
  • 执行耗时
  • Token 消耗
  • 中间结果预览
```

---

## 9. Phase 7 Human-in-the-Loop — 企业级增强

### 9.1 审批工作流引擎

```
审批配置 DSL:

# agent_config.interrupt_on
interrupt_rules:
  - id: "sensitive_write"
    match:
      tool: ["write_file", "execute_command", "delete_file"]
    approval:
      type: "single|quorum|senior"
      quorum_count: 2          # quorum 模式需要的审批人数
      senior_role: "admin"     # senior 模式需要 admin 审批
      timeout: 300             # 5 分钟超时 → 自动拒绝
      timeout_policy: "reject|auto_approve"
      channels:                # 通知渠道
        - "web"
        - "wechat"
        
  - id: "high_cost_decision"
    match:
      estimated_cost_gt: 0.50  # 预估超过 $0.50
    approval:
      type: "single"
      timeout: 120

审批流程状态机:
  pending → approved → executing → completed
       │         │
       └─────→ rejected → fallback_action
       │
       └─────→ timeout → timeout_policy
```

### 9.2 审批通知系统

```
┌─────────────────────────────────────────────┐
│        Notification Dispatcher               │
│                                             │
│  审批请求 → 查找审批人 → 多渠道推送            │
│             │                               │
│    ┌────────┼────────┬────────────┐         │
│    ▼        ▼        ▼            ▼         │
│  Web UI  WeChat   Feishu     DingTalk       │
│  (实时)  (模板消息) (卡片消息)  (ActionCard)   │
│                                             │
│  消息模板: "Agent 'X' 请求执行 'write_file'  │
│            [批准] [拒绝] [查看详情]"           │
│                                             │
│  审批超时处理:                                │
│  • 30s 后催促通知                            │
│  • 5min 后自动执行 timeout_policy            │
│  • 记录审计日志                               │
└─────────────────────────────────────────────┘
```

### 9.3 权限系统完整实现

```
权限检查管道:

  Request → API Gateway
              │
              ▼
          JWT 验证 (签名 + 过期)
              │
              ▼
          Tenant 解析 (X-Tenant-ID + JWT claims 交叉检查)
              │
              ▼
          Permission Checker
              │
    ┌─────────┼──────────┐
    ▼         ▼          ▼
  RBAC    Scope       Quota
  Check   Check       Check
              │
              ▼
          Allowed / Denied
              │
              ▼
          审计日志记录

资源级权限示例:
  • Agent "support-bot": user_1(RW), user_2(R), user_3(-)
  • 对话 "conv_123": user_1(owner), user_2(RW)
  • Skill "custom-skill": tenant_users(R), tenant_admins(RW)

权限同步到 DeepAgents:
  • 文件系统权限: Permissions(read_domains, write_domains)
  • 工具权限: allowed_tools, disallowed_tools
  • 子 Agent 权限: 继承父 Agent 权限，可选缩减
```

---

## 10. Phase 8 运维监控 — 企业级增强

### 10.1 自托管可观测性栈

```
自建机房完整监控栈:

┌─────────────────────────────────────────────────────────────┐
│                    Observability Stack (All Self-Hosted)     │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Metrics   │  │Logging   │  │Tracing   │  │Alerting  │  │
│  │          │  │          │  │          │  │          │  │
│  │Prometheus│  │Loki      │  │Tempo     │  │AlertMgr  │  │
│  │+ Node    │  │+ Promtail│  │+ OTEL    │  │+ Webhook │  │
│  │Exporter  │  │          │  │Collector │  │          │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │              │              │              │       │
│       └──────────────┴──────────────┴──────────────┘       │
│                          │                                  │
│                          ▼                                  │
│                   ┌──────────────┐                         │
│                   │   Grafana    │                         │
│                   │  Dashboards  │                         │
│                   └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘

关键指标面板:

1. 服务健康
   ├── 请求量 (RPS per endpoint)
   ├── 响应延迟 (p50/p90/p99)
   ├── 错误率 (4xx/5xx 分类)
   └── 活跃连接数 (WebSocket / SSE)

2. 智能体性能
   ├── Agent 活跃数
   ├── 对话轮次
   ├── 平均响应时间
   ├── 工具调用次数 / 成功率
   ├── Token 消耗 (按 Model/Agent 分组)
   └── 并发 Agent 数

3. 基础设施
   ├── CPU / 内存 / 磁盘 (per node)
   ├── GPU 利用率 / 显存
   ├── PostgreSQL 连接池 / 慢查询 / 死锁
   ├── Redis 命中率 / 内存使用
   └── 网络吞吐量

4. 业务指标
   ├── 租户活跃度 (日活/周活/月活)
   ├── Skills 安装数 / 使用率
   ├── 通道消息量 (per channel)
   └── 成本概览 (per tenant/model)
```

### 10.2 告警规则

```
告警分级:

┌────────┬──────────────────────────────────────┐
│ P0 紧急 │ 服务完全不可用 / 数据库宕机             │
│        │ → 立即电话 + 即时通讯 + 邮件            │
├────────┼──────────────────────────────────────┤
│ P1 严重 │ 错误率 > 5% / Agent 全部异常           │
│        │ → 即时通讯 + 邮件                      │
├────────┼──────────────────────────────────────┤
│ P2 警告 │ Token 用量 > 80% / 磁盘 > 80%         │
│        │ → 邮件                                │
├────────┼──────────────────────────────────────┤
│ P3 通知 │ 新版本可用 / 定期报告                   │
│        │ → 邮件聚合 (每日/每周)                   │
└────────┴──────────────────────────────────────┘

具体告警规则:
  • service_down > 1 min → P0
  • error_rate_5xx > 5% for 5 min → P1
  • agent_queue_depth > 100 → P2
  • llm_provider_error_rate > 10% → P1
  • db_connection_pool_exhausted → P1
  • redis_memory > 80% → P2
  • disk_free < 20% → P2
  • tenant_token_exhausted → P2 (仅通知该租户管理员)
```

### 10.3 日志规范

```
结构化日志格式 (JSON):

{
  "timestamp": "2026-05-09T10:30:00.123Z",
  "level": "INFO|WARN|ERROR|DEBUG",
  "logger": "app.api.agents",
  "message": "Agent created",
  "request_id": "req_abc123",
  "tenant_id": "tenant_xyz",
  "user_id": "user_001",
  "trace_id": "trace_abc",        // OpenTelemetry trace ID
  "span_id": "span_001",
  "context": {
    "agent_id": "agent_001",
    "action": "agent.create",
    "duration_ms": 150
  }
}

日志级别策略:
  • ERROR: 需要立即关注的故障（对应 P0/P1 告警）
  • WARNING: 潜在问题（对应 P2 告警）
  • INFO: 关键业务流程节点
  • DEBUG: 仅开发环境启用

日志轮转:
  • Docker: json-file → Loki (Docker driver)
  • 裸机: logrotate (daily, keep 30 days, compress)
  • 审计日志: 永久保留（冷归档）
```

---

## 11. Phase 9 企业级后台管理（新增）

### 11.1 Admin Dashboard

```
后台功能模块:

┌─────────────────────────────────────────────┐
│              Admin Dashboard                 │
├─────────────────────────────────────────────┤
│                                             │
│  1. 租户管理                                  │
│  ├── 租户列表（搜索/筛选/排序）                │
│  ├── 创建/停用/删除租户                        │
│  ├── 租户配额配置（Token/Agent/存储）          │
│  └── 租户使用概览                             │
│                                             │
│  2. 用户管理                                  │
│  ├── 用户列表                                 │
│  ├── 角色管理 + 权限分配                       │
│  ├── MFA 管理（重置/禁用）                     │
│  └── 登录历史 / 会话管理                       │
│                                             │
│  3. 系统监控                                  │
│  ├── 实时服务状态                             │
│  ├── 资源使用趋势                             │
│  ├── 告警历史                                 │
│  └── 成本分析面板                             │
│                                             │
│  4. 审计日志                                  │
│  ├── 全局审计日志检索                          │
│  ├── 按租户/用户/操作过滤                      │
│  ├── 敏感操作报告                             │
│  └── 日志导出 (CSV/JSON)                      │
│                                             │
│  5. 系统配置                                  │
│  ├── 全局参数配置                             │
│  ├── Feature Flags 管理                      │
│  ├── 全局 Skills 管理                         │
│  ├── 邮件/通知模板管理                         │
│  └── 数据保留策略                              │
│                                             │
│  6. Skills 审核                               │
│  ├── 待审核 Skills 队列                        │
│  ├── 安全扫描结果                             │
│  ├── 审核操作（通过/拒绝/修改）                 │
│  └── Skills 举报处理                          │
│                                             │
│  7. 通道管理                                  │
│  ├── 全局通道状态                             │
│  ├── 通道 Provider 配置                        │
│  └── 通道 Webhook 日志                        │
└─────────────────────────────────────────────┘
```

### 11.2 Feature Flags

```
特性开关管理:

使用场景:
  • 灰度发布新功能
  • 按租户开启实验性功能
  • 紧急关闭有问题的功能

Flag 配置:
  ┌─────────────────────────────────────────────┐
  │ flags:                                      │
  │   multi_agent_orchestration:                │
  │     enabled: true                           │
  │     roll_out:                               │
  │       - tenants: ["tenant_a", "tenant_b"]   │
  │         percentage: 100                      │
  │       - tenants: ["*"]                       │
  │         percentage: 20                       │
  │                                              │
  │   skills_market_v2:                         │
  │     enabled: false                           │
  │     reason: "等待安全审计完成"                │
  │                                              │
  │   wechat_channel:                            │
  │     enabled: true                            │
  │     tenants: ["tenant_enterprise_*"]         │
  └─────────────────────────────────────────────┘

实现:
  • 存储: PostgreSQL (flags 表) + Redis 缓存
  • 后端: 中间件注入 feature flag context
  • 前端: API endpoint /api/admin/flags/resolve
  • 管理: Admin Dashboard 可视化开关
```

---

## 12. Phase 10 安全合规加固（新增）

### 12.1 安全扫描与防护

```
安全防护体系:

Layer 1 - 网络层:
  • Traefik TLS termination (Let's Encrypt 自动续期)
  • WAF 规则 (ModSecurity / Coraza)
  • DDoS 防护 (IP-based rate limiting)
  • 仅暴露必要端口 (443, 可选 SSH bastion)

Layer 2 - 应用层:
  • JWT 验证 + RBAC + RLS
  • CSP 头 + CORS 严格配置
  • SQL 注入: SQLAlchemy 参数化查询
  • XSS: 前端输出转义
  • CSRF: SameSite cookies + CSRF token
  • SSRF: 出站请求白名单

Layer 3 - 数据层:
  • 传输加密: TLS 1.3
  • 静态加密: PostgreSQL TDE 或磁盘 LUKS
  • API Key: AES-256-GCM 加密存储
  • 密码: bcrypt/argon2 哈希
  • PII 数据: 可选的列级加密

Layer 4 - 运行时:
  • 容器非 root 运行
  • 只读根文件系统
  • Seccomp / AppArmor 策略
  • 资源限制 (CPU/Memory Cgroups)
  • 定期 CVE 扫描 (Trivy)
```

### 12.2 合规性支持

```
合规框架映射:

┌──────────────┬──────────────────────────────┐
│ GDPR         │ • PII 数据标记与加密           │
│              │ • 用户数据导出 (Right to Access)│
│              │ • 数据删除 (Right to Erasure)  │
│              │ • 数据处理记录 (Art. 30)       │
├──────────────┼──────────────────────────────┤
│ SOC 2        │ • 审计日志完整性                │
│              │ • 访问控制审查                  │
│              │ • 变更管理记录                  │
│              │ • 事件响应流程                  │
├──────────────┼──────────────────────────────┤
│ ISO 27001    │ • 资产清单                     │
│              │ • 风险评估                     │
│              │ • 供应商安全评估                │
│              │ • 持续监控                     │
└──────────────┴──────────────────────────────┘

数据保留策略 (可配置):
  • 对话记录: 默认 90 天，租户可配置
  • 审计日志: 默认 1 年，合规要求 > 3 年
  • 已删除租户数据: 30 天软删除 → 90 天后物理删除
  • Token 用量: 永久 (仅统计数据，不含消息内容)
```

### 12.3 安全事件响应

```
事件响应 SOP:

Detection → 告警触发
    │
    ▼
Triage → 评估严重性 (P0-P3)
    │
    ▼
Containment → 隔离受影响租户/服务
    │
    ▼
Investigation → 审计日志分析 → 根因定位
    │
    ▼
Remediation → 修复 + 补丁 + 回滚
    │
    ▼
Post-Mortem → 事后报告 + 预防措施

自动化响应:
  • 检测到暴力登录 → 自动启用 CAPTCHA + IP 封禁
  • 检测到异常 Token 消耗 → 自动暂停 Agent + 通知管理员
  • 容器崩溃 > 3 次 → 自动回滚到上一个稳定版本
```

---

## 13. Phase 11 高可用与灾备（新增）

### 13.1 自建机房高可用架构

```
高可用部署拓扑:

                     Load Balancer (Keepalived VIP)
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
      ┌──────────┐   ┌──────────┐   ┌──────────┐
      │ Traefik  │   │ Traefik  │   │ Traefik  │
      │ Node-1   │   │ Node-2   │   │ Node-3   │
      │ (Active) │   │ (Active) │   │ (Active) │
      └────┬─────┘   └────┬─────┘   └────┬─────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
 ┌──────────┐       ┌──────────┐        ┌──────────┐
 │Backend-1 │       │Backend-2 │        │Backend-3 │
 │(FastAPI) │       │(FastAPI) │        │(FastAPI) │
 └────┬─────┘       └────┬─────┘        └────┬─────┘
      │                   │                    │
      └───────────────────┼────────────────────┘
                          │
       ┌──────────────────┼──────────────────┐
       ▼                  ▼                  ▼
 ┌──────────┐      ┌──────────┐       ┌──────────┐
 │PostgreSQL│      │  Redis   │       │ MinIO    │
 │ 主-备     │      │ Sentinel │       │ 集群     │
 │ (Patroni)│      │  集群    │       │          │
 └──────────┘      └──────────┘       └──────────┘

关键设计:
  • 无状态后端: 任意节点可处理请求
  • 数据库: Patroni + etcd 实现自动故障切换
  • Redis: Sentinel 3 节点实现自动故障切换
  • 存储: MinIO 分布式模式 / NFS 共享存储
  • 会话: JWT 无状态 + Redis 黑名单 (可容忍 Redis 短暂不可用)
```

### 13.2 备份与恢复

```
备份策略:

┌──────────────────────────────────────────────┐
│ Database (PostgreSQL)                         │
│  • 全量备份: 每日 02:00 (pg_dump, 保留 30 天)  │
│  • WAL 归档: 持续 (PITR, 可恢复到任意时间点)    │
│  • 备份验证: 每周自动还原测试                    │
│  • 异地备份: 通过 rsync/scp 同步到异地存储      │
├──────────────────────────────────────────────┤
│ 文件存储 (工作目录/Skills)                     │
│  • 增量备份: 每日 (rclone sync, 保留 90 天)    │
│  • 快照: MinIO bucket versioning              │
├──────────────────────────────────────────────┤
│ 配置文件 + 密钥                                │
│  • Vault snapshot: 每日 + 事件触发             │
│  • Git 仓库: 所有配置 IaC                     │
│  • 密钥: Vault 自动备份 (加密)                 │
└──────────────────────────────────────────────┘

恢复流程:
  1. 基础设施恢复 (Terraform/Ansible + Docker Compose)
  2. Database PITR 恢复到目标时间点
  3. 文件存储从 MinIO 备份同步
  4. Vault 密钥恢复 + 解封
  5. 服务启动 + 健康检查
  6. 冒烟测试自动化验证

RTO/RPO 目标:
  • RTO (恢复时间): < 1 小时 (数据库 + 服务)
  • RPO (数据丢失): < 5 分钟 (WAL 归档间隔)
  • 重大灾难: RTO < 4 小时, RPO < 1 小时
```

### 13.3 优雅降级策略

```
服务降级矩阵:

┌─────────────────┬─────────────────────────────┐
│ 故障场景          │ 降级策略                      │
├─────────────────┼─────────────────────────────┤
│ LLM Provider 故障 │ 自动 Fallback 到备用 Provider │
│                 │ → 全部不可用 → 返回"服务繁忙"  │
├─────────────────┼─────────────────────────────┤
│ PostgreSQL 故障   │ 只读模式: Checkpoint 历史对话  │
│                 │ 不可用: 新对话返回错误          │
├─────────────────┼─────────────────────────────┤
│ Redis 故障        │ 限流失效 → 切换到内存限流      │
│                 │ 缓存穿透 → 直接查数据库(小心!)  │
├─────────────────┼─────────────────────────────┤
│ 文件存储故障      │ 新文件: 暂存本地 → 恢复后同步  │
│                 │ 已存在: 从缓存/DB 中读取备用    │
├─────────────────┼─────────────────────────────┤
│ 单节点故障        │ 负载均衡自动切换              │
│                 │ 会话: JWT 保证无状态           │
└─────────────────┴─────────────────────────────┘

熔断器配置:
  • LLM API: 错误率 > 50% → 熔断 30s → 半开 → 恢复
  • 通道 Webhook: 连续失败 5 次 → 熔断 2 min → 半开
  • 数据库: 连接超时 > 10s → 熔断 → 快速失败
```

---

## 14. 非功能需求矩阵

| 需求 | 目标 | 衡量方式 |
|------|------|---------|
| **响应时间** | P95 < 2s (简单对话), < 30s (Agent 工具链) | Prometheus Histogram |
| **吞吐量** | 100+ 并发对话/节点 | Load Test (Locust/k6) |
| **可用性** | 99.9% (月宕机 < 43min) | Uptime Monitor |
| **数据持久性** | 99.99% | 备份验证报告 |
| **扩展性** | 水平扩展至 10 节点 | Kubernetes Cluster |
| **安全性** | OWASP Top 10 全防御 + 渗透测试通过 | 安全扫描报告 |
| **Token 效率** | Agent 平均每次对话 < 5000 tokens | Token Tracker |
| **代码覆盖率** | 整体 > 75%, 核心 > 90% | pytest-cov |
| **部署频率** | 周部署, 紧急修复 < 2h | CI/CD Log |

---

## 总结：企业级与实践路线的映射

```
核心设计决策回顾:
  • 多租户: Shared DB + RLS → 低成本 + 强隔离
  • 认证: OAuth2 + JWT → 自建、可控
  • 测试: 务实均衡 → 高价值覆盖
  • 部署: 自建机房 → 全自托管技术栈

项目目录结构演进:

practice/aethermind/
├── docker-compose.yml              → docker-compose.prod.yml (高可用)
├── .env.example                    → 多环境配置
├── helm/                            (新增) K8s Helm Chart
├── ansible/                         (新增) 自动化部署
├── terraform/                       (新增) IaC 基础设施
├── backend/
│   ├── alembic/                     (新增) 数据库迁移
│   ├── tests/                       (新增) 测试套件
│   └── app/
│       ├── auth/                    (新增) 认证模块
│       ├── admin/                   (新增) 后台管理
│       ├── channels/                (新增) 通道模块
│       ├── core/
│       │   ├── security.py         (新增) 安全中间件
│       │   ├── tenant.py           (新增) 租户上下文
│       │   ├── audit.py            (新增) 审计日志
│       │   └── feature_flags.py    (新增) 特性开关
│       └── ...
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── admin/               (新增) 后台管理页
│       │   └── ...
│       └── ...
├── monitoring/                      (新增) Grafana Dashboard JSON
├── nginx/                           Traefik 配置
├── scripts/                         (新增) 运维脚本
└── docs/
    └── enterprise-architecture.md   ← 本文档
```

实施建议：Phase 0（企业基础设施）应作为最高优先级，在所有业务 Phase 之前建立。
