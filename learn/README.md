# LangChain + LangGraph + DeepAgents 学习计划

---

## 最终学习目标与能力画像

完成全部学习后，你将具备以下能力：

| 能力维度 | 具体表现 |
|---------|---------|
| **智能体架构设计** | 能独立设计并实现生产级多智能体系统，理解规划、记忆、工具调用、子智能体协作的完整链路 |
| **框架深度掌握** | 精通 LangChain 核心抽象（ChatModel/Tool/Chain/Memory/RAG），精通 LangGraph 状态图编排（StateGraph/Checkpointing/Human-in-the-Loop/Streaming），精通 DeepAgents 全套能力（Planning/Subagents/Skills/Virtual Filesystem/Sandbox） |
| **工程化能力** | 能构建完整的前后端分离智能体平台，包含数据库设计、API 设计、前端交互、消息队列、容器化部署 |
| **通道集成** | 能实现 REST/WebSocket/Webhook 多通道统一接入层，支持企业微信、钉钉、飞书等 |
| **Skills 生态** | 理解 Agent Skills 规范，能独立开发、分发、管理 Skills |
| **生产运维** | 掌握 LangSmith 全链路追踪、监控告警、容错重试、持久化恢复 |

---

## 阶段一：LangChain 核心基础（第 1-2 周）

**目标：掌握 LLM 应用开发的核心抽象**

- [ ] **Chat Models**: `init_chat_model` 统一接口，支持 OpenAI / Anthropic / Google / 本地模型切换
- [ ] **Prompt Templates**: ChatPromptTemplate、MessagesPlaceholder、Few-shot prompting
- [ ] **Tools**: `@tool` 装饰器、StructuredTool、Tool 参数校验、工具组合
- [ ] **Chains**: LCEL（LangChain Expression Language）、RunnableSequence、RunnableParallel、RunnablePassthrough
- [ ] **Memory**: ConversationBufferMemory、ConversationSummaryMemory、向量记忆
- [ ] **RAG 全流程**: Document Loader → Text Splitter → Embeddings → VectorStore → Retriever → QA Chain
- [ ] **Callbacks**: 自定义 Callback、LangSmith 追踪集成
- [ ] **Streaming**: token-level streaming、astream_events

**验收标准**：能用 LangChain 独立完成一个带 RAG 和工具调用的单智能体问答系统。

### 练习脚本索引

| 编号 | 文件 | 内容 |
|------|------|------|
| 01 | `01_chat_models.py` | 多 Provider 模型切换与基本对话 |
| 02 | `02_prompt_templates.py` | ChatPromptTemplate / Few-shot / MessagesPlaceholder |
| 03 | `03_tools.py` | @tool 装饰器 / StructuredTool / 多工具组合 |
| 04 | `04_chains_lcel.py` | LCEL / RunnableSequence / RunnableParallel |
| 05 | `05_memory.py` | ConversationBufferMemory / SummaryMemory |
| 06 | `06_rag.py` | Document Loader → Splitter → Embeddings → VectorStore → QA |
| 07 | `07_callbacks.py` | 自定义 Callback / LangSmith 追踪 |
| 08 | `08_streaming.py` | token-level streaming / astream_events |
| 09 | `09_agent_final.py` | 综合验收：RAG + Tool Use 单智能体 |

---

## 阶段二：LangGraph 状态图编排（第 3-4 周）

**目标：掌握有状态多步骤智能体编排**

- [ ] **核心概念**: StateGraph、Node、Edge、Conditional Edge、State Schema (TypedDict)
- [ ] **节点设计**: 单一职责节点、节点间数据传递、并行节点 (Send API)
- [ ] **条件路由**: `add_conditional_edges`、基于 LLM 的路由决策
- [ ] **Checkpointing**: MemorySaver、SqliteSaver、PostgresSaver，任意节点故障恢复
- [ ] **Human-in-the-Loop**: `interrupt()` / `interrupt_before` / `interrupt_after`、`Command()` 恢复
- [ ] **Streaming**: `stream_mode`（values/updates/custom/messages/debug）
- [ ] **Subgraph**: `add_node` 嵌套子图、图间通信
- [ ] **最佳实践模式**:
  - Supervisor Agent Pattern（监督者智能体模式）
  - Hierarchical Agent Teams（层级智能体团队）
  - Map-Reduce Agent Pattern（分治智能体模式）
  - Swarm / Handoff Pattern（移交智能体模式）

**验收标准**：能设计并实现一个包含 3+ 节点的多步智能体工作流，支持人机协同和断点恢复。

---

## 阶段三：DeepAgents 高级智能体（第 5-6 周）

**目标：掌握生产级智能体的全部能力**

- [ ] **核心架构认知**：DeepAgents = LangGraph Runtime + 内置工具 + 规划 + 文件系统 + 子智能体
- [ ] **create_deep_agent**: 完整参数理解，model / tools / system_prompt / middleware / skills / memory / permissions / backend / interrupt_on
- [ ] **Virtual Filesystem**: StateBackend / FilesystemBackend / StoreBackend / Sandbox Backend，Composite Backend
- [ ] **Planning System**: built-in `write_todos` 工具，任务分解与追踪
- [ ] **Subagents**: `task` 工具自动生成子智能体、自定义 SubAgent、上下文隔离
- [ ] **Skills 体系**: Agent Skills 规范（SKILL.md + scripts + docs + assets），渐进式披露
- [ ] **Permissions**: 文件系统权限规则、读写控制、子智能体继承
- [ ] **Memory**: 跨线程持久记忆、LangGraph Store
- [ ] **Profiles**: HarnessProfile、系统提示组装（USER → BASE/CUSTOM → SUFFIX）
- [ ] **Human-in-the-Loop**: `interrupt_on` 配置、敏感操作审批
- [ ] **Sandboxes**: Modal / Daytona / Deno 沙箱执行环境
- [ ] **Middleware**: 内置中间件（TodoList / Filesystem / SubAgent / Summarization / Ping），自定义中间件开发

**验收标准**：能创建一个 Deep Agent，具备自定义工具、Skills、Filesystem Backend、子智能体生成、敏感操作审批能力。

---

## 阶段四：生态与集成（第 7-8 周）

- [ ] **LangSmith**: 全链路追踪、数据集评估、线上监控
- [ ] **LangServe**: 将 Agent 部署为 REST API
- [ ] **MCP 协议**: Model Context Protocol 集成
- [ ] **ACP 协议**: Agent Client Protocol（编辑器集成）
- [ ] **多模型路由**: 基于成本/速度/能力的动态模型选择
- [ ] **向量数据库集成**: Chroma / Milvus / Pinecone / Qdrant

---

## 最终能力验证清单

完成全部学习后，你将能够：

- [ ] 用 LangChain 快速搭建 RAG + Tool Use 单智能体
- [ ] 用 LangGraph 设计复杂多步骤智能体工作流，含人机协同
- [ ] 用 DeepAgents 构建具备规划、记忆、文件系统、子智能体的生产级 Agent

---

## 推荐学习资源

| 资源 | 链接 |
|------|------|
| LangChain 官方文档 | https://docs.langchain.com/oss/python/langchain |
| LangGraph 官方文档 | https://docs.langchain.com/oss/python/langgraph |
| DeepAgents 官方文档 | https://docs.langchain.com/oss/python/deepagents |
| Agent Skills 规范 | https://agentskills.io/specification |
| LangChain Skills 仓库 | https://github.com/langchain-ai/langchain-skills |
| DeepAgents 源码 | https://github.com/langchain-ai/deepagents |
| LangSmith | https://smith.langchain.com |
