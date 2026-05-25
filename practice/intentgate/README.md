# IntentGate

多通道卡片交互网关。完整文档见 **[docs/intentgate](../../docs/intentgate/README.md)**。

## 快速开始

```bash
cd practice/intentgate
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e .
cp .env.example .env
uvicorn intentgate.main:app --reload --port 8090
```

- 健康检查：`GET http://127.0.0.1:8090/health`
- 协议说明：`GET http://127.0.0.1:8090/api/v1/protocol`

## 文档

| 文档 | 说明 |
|------|------|
| [文档中心](../../docs/intentgate/README.md) | 索引 |
| [项目规划](../../docs/intentgate/01-项目规划.md) | 里程碑与范围 |
| [架构设计](../../docs/intentgate/02-架构设计.md) | 分层与数据流 |
| [协议规范](../../docs/intentgate/03-协议规范.md) | CardIntent / API |
| [通道与客户端](../../docs/intentgate/04-通道与客户端.md) | 企微 / 飞书 / Web |
| [卡片系统](../../docs/intentgate/05-卡片系统.md) | YAML 模板与 Runtime |
| [Agent 后端对接](../../docs/intentgate/06-Agent后端对接.md) | AgentScope / AetherMind |
| [实施与运维](../../docs/intentgate/07-实施与运维.md) | 部署与 checklist |
| [代码文件说明](../../docs/intentgate/08-代码文件说明.md) | 文件清单与阅读顺序 |
