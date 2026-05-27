# 阶段一：LangChain 核心基础 - 学习指南

> **LangChain v1.2.x** · 使用最新 `create_agent` / `langchain.messages` / `langchain.tools` / `langchain-chroma`

## 项目结构总览

```
c:\code\langchain\
├── learn/                              # ← 学习项目（当前阶段）
│   ├── README.md                       # 完整学习计划（4 阶段）
│   ├── stage-1.md                      # 当前文件：阶段一指南
│   └── langchain/                      # LangChain 阶段一练习
│       ├── .env                        # API Key 配置
│       ├── requirements.txt            # Python 依赖（v1.2.x）
│       ├── model.py                    # 模型工厂
│       ├── 01_chat_models.py           # 多 Provider 模型切换
│       ├── 02_prompt_templates.py      # Prompt 模板系统
│       ├── 03_tools.py                 # 工具定义与使用
│       ├── 04_chains_lcel.py           # LCEL 管道表达式
│       ├── 05_memory.py                # 对话记忆系统
│       ├── 06_rag.py                   # RAG 检索增强生成
│       ├── 07_callbacks.py             # 回调系统与追踪
│       ├── 08_streaming.py             # 流式输出
│       ├── 09_agent_final.py           # ★ 综合验收 (v1 create_agent)
│       ├── 10_check_pointer.py         # Checkpointer 对话记忆
│       ├── 11_stream_memory.py         # 带记忆的 token 流
│       └── 12_structured_output.py     # 结构化输出
│
└── practice/                           # ← 实践项目
    ├── README.md                       # 项目索引
    ├── aethermind/                     # AetherMind 智能体平台（Phase 1 已完成）
    └── intentgate/                     # IntentGate 多通道卡片网关
```

## 启动学习

```bash
# 1. 进入 LangChain 练习目录
cd c:\code\langchain\learn\langchain

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key（至少配置一个）
# 编辑 .env，填入:
#   OPENAI_API_KEY=sk-xxx
#   (可选) ANTHROPIC_API_KEY / GOOGLE_API_KEY

# 4. 按顺序运行练习
python 01_chat_models.py
python 02_prompt_templates.py
python 03_tools.py
python 04_chains_lcel.py
python 05_memory.py
python 06_rag.py
python 07_callbacks.py
python 08_streaming.py
python 09_agent_final.py
python 10_check_pointer.py
python 11_stream_memory.py
python 12_structured_output.py
```

## 练习脚本速览

| 编号 | 文件 | 核心知识点 | 需 API |
|------|------|-----------|:---:|
| 01 | `langchain/01_chat_models.py` | `init_chat_model` 统一接口，支持 OpenAI / Anthropic / Google / Ollama 多 Provider 切换 | ✓ |
| 02 | `langchain/02_prompt_templates.py` | ChatPromptTemplate / Few-shot prompting / MessagesPlaceholder / PipelinePrompt | 部分 |
| 03 | `langchain/03_tools.py` | `@tool` 装饰器 / StructuredTool / `model.bind_tools()` 工具绑定 | 部分 |
| 04 | `langchain/04_chains_lcel.py` | `\|` 管道操作符 / RunnableParallel 并行 / RunnablePassthrough 透传 / RunnableLambda 自定义函数 | ✓ |
| 05 | `langchain/05_memory.py` | RunnableWithMessageHistory 历史管理 / SummaryMemory 摘要压缩 / trim_messages 智能裁剪 | 部分 |
| 06 | `langchain/06_rag.py` | Document Loader → Text Splitter → Embeddings → VectorStore → Retriever → QA 完整链路 | ✓ |
| 07 | `langchain/07_callbacks.py` | BaseCallbackHandler 自定义回调 / Token 计数 / LangSmith 全链路追踪 | ✓ |
| 08 | `langchain/08_streaming.py` | `.stream()` / `.astream()` / `.astream_events()` / stream_mode 六种模式对比 | ✓ |
| 09 | `langchain/09_agent_final.py` | **综合验收 (v1)**: `create_agent` + Checkpointer 记忆 + `stream_mode='updates'` | ✓ |
| 10 | `langchain/10_check_pointer.py` | `InMemorySaver` / `SqliteSaver`、`get_state` / `update_state`、摘要写回、历史裁剪 | 部分 |
| 11 | `langchain/11_stream_memory.py` | Agent + checkpointer + `stream_mode='messages'` 逐 token 流式多轮记忆 | ✓ |
| 12 | `langchain/12_structured_output.py` | `with_structured_output` / `response_format` / Pydantic / ToolStrategy | ✓ |

## 学习目标

完成阶段一全部练习后，你将掌握 LangChain v1 的核心抽象：

- **Chat Models** — 用统一的 `init_chat_model` 接口调用任意 LLM（OpenAI/Claude/Gemini/Ollama）
- **Prompt Templates** — 结构化提示模板、Few-shot 少样本引导、对话历史动态注入
- **Tools** — 用 `@tool` 装饰器定义工具，让 LLM 自主选择调用
- **Chains (LCEL)** — 用 `|` 管道串联组件，并行执行，透传数据
- **Memory** — 对话历史管理（RunnableWithMessageHistory / checkpointer）、摘要压缩、智能裁剪
- **RAG** — 从文档加载到向量检索到增强生成的完整流水线
- **Callbacks** — 自定义回调监控耗时和 Token，集成 LangSmith 全链路追踪
- **Streaming** — 逐 Token 实时输出，6 种 stream_mode，支持 SSE/WebSocket 等场景

## 验收标准

能独立完成一个 **RAG + Tool Use + Memory** 的单智能体问答系统（使用 `create_agent` + `checkpointer` + `stream_mode`）。

## v1 vs 旧版本速查

| 旧写法 | v1 新写法 |
|--------|-----------|
| `langchain_core.messages.HumanMessage` | `langchain.messages.HumanMessage` |
| `langchain_core.tools.tool` | `langchain.tools.tool` |
| `langchain_core.callbacks.BaseCallbackHandler` | `langchain.callbacks.BaseCallbackHandler` |
| `langgraph.prebuilt.create_react_agent` | `langchain.agents.create_agent` |
| `langchain_community.vectorstores.Chroma` | `langchain_chroma.Chroma` |
| `RunnableWithMessageHistory` (Agent) | `checkpointer + thread_id` |
| `AgentExecutor` / 手写执行循环 | `create_agent` 自动处理 |
| `stream_mode='values'` only | `values` / `updates` / `messages` / `custom` / `debug` |
