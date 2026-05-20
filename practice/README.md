# Practice 实践项目

本目录包含 LangChain 学习仓库中的可运行实践项目。

| 项目 | 说明 | 文档 |
|------|------|------|
| [AetherMind](./aethermind/) | 内部智能体管理开发平台 | [docs/aethermind](../docs/aethermind/README.md) |
| [IntentGate](./intentgate/) | 多通道卡片交互网关 | [docs/intentgate](../docs/intentgate/README.md) |

## 关系

```
IM 客户端 → IntentGate（卡片/通道）→ AetherMind（Agent 推理）→ 业务 API
Web UI  ──────────────────────────→ AetherMind
```
