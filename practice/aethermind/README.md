# AetherMind

公司内部智能体管理开发平台。完整文档见 **[docs/aethermind](../../docs/aethermind/README.md)**。

## 快速启动

```bash
cd practice/aethermind
cp .env.example .env
# 编辑 .env，配置 OPENAI_API_KEY 等
docker-compose up -d
```

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:3000 |
| API 文档 | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/api/health |

## 文档

| 文档 | 说明 |
|------|------|
| [文档中心](../../docs/aethermind/README.md) | 索引 |
| [项目规划](../../docs/aethermind/01-项目规划.md) | 定位与路线图 |
| [架构设计](../../docs/aethermind/02-架构设计.md) | 分层与数据流 |
| [数据模型与 API](../../docs/aethermind/03-数据模型与API.md) | ORM、REST、SSE |
| [智能体运行时](../../docs/aethermind/04-智能体运行时.md) | AgentRuntime、ModelHub |
| [阶段能力规划](../../docs/aethermind/05-阶段能力规划.md) | Phase 2–9 |
| [IntentGate 集成](../../docs/aethermind/06-IntentGate集成.md) | IM 卡片对接 |
| [企业加固规划](../../docs/aethermind/07-企业加固规划.md) | 延后批次 |
| [对标 Hermes 与规划修订](../../docs/aethermind/09-对标Hermes与规划修订.md) | **Phase 排期权威** |
| [实施与运维](../../docs/aethermind/08-实施与运维.md) | 部署与交付状态 |

## 相关项目

- [IntentGate](../intentgate/) — 多通道卡片交互网关
