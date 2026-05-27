"""
10_check_pointer.py - Checkpointer 对话记忆 (v1)

学习要点:
1. InMemorySaver / SqliteSaver: 会话状态持久化
2. thread_id: 会话隔离键（对应 05 的 session_id）
3. with_checkpointer: 为 Agent 自动保存/恢复对话状态
4. get_state / update_state: 读取与写回历史（裁剪、摘要）
5. 与 05_memory.py 对比: RunnableWithMessageHistory → checkpointer + thread_id

05_memory.py 使用 RunnableWithMessageHistory 管理 Chain 历史;
本脚本使用 LangGraph Checkpointer 管理 Agent 状态，是 v1 推荐写法。
"""
import os
import tempfile
from dotenv import load_dotenv

load_dotenv()

from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    trim_messages,
    RemoveMessage,
)
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import REMOVE_ALL_MESSAGES


# ========== 1. 构建带 Checkpointer 的对话 Agent ==========

def build_agent_with_memory(
    model_name: str = "openai:gpt-4o",
    temperature: float = 0.7,
    checkpointer=None,
):
    """创建带 checkpointer 的 Agent；不传则使用 InMemorySaver"""
    model = init_chat_model(model_name, temperature=temperature)
    cp = checkpointer or InMemorySaver()
    agent = create_agent(
        model=model,
        tools=[],
        system_prompt="你是一个友好的助手。",
        checkpointer=cp,
    )
    return agent


def thread_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def chat(agent, user_input: str, thread_id: str) -> str:
    """单轮对话，通过 thread_id 自动带上历史"""
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_input}]},
        config=thread_config(thread_id),
    )
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.content:
            if not (hasattr(msg, "tool_calls") and msg.tool_calls):
                return msg.content
    return ""


def get_thread_messages(agent, thread_id: str) -> list:
    """从 checkpointer 读取会话消息（对应 05 的 get_session_history）"""
    state = agent.get_state(config=thread_config(thread_id))
    if state and state.values:
        return list(state.values.get("messages", []))
    return []


def replace_thread_messages(agent, thread_id: str, new_messages: list) -> None:
    """用 update_state 整体替换会话消息（先清空再写入）"""
    agent.update_state(
        thread_config(thread_id),
        {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *new_messages]},
    )


def trim_and_persist(agent, thread_id: str, max_tokens: int = 120) -> tuple[int, int]:
    """get_state → trim_messages → update_state 闭环"""
    messages = get_thread_messages(agent, thread_id)
    before = len(messages)
    trimmed = trim_messages(
        messages,
        max_tokens=max_tokens,
        strategy="last",
        token_counter=len,
        include_system=True,
        allow_partial=False,
        start_on="human",
    )
    replace_thread_messages(agent, thread_id, trimmed)
    return before, len(trimmed)


# ========== 2. Demo: 全量缓冲记忆 (对应 05 demo_buffer_memory) ==========

def demo_buffer_memory():
    """Checkpointer 全量记忆: 同一 thread_id 下自动保留完整对话"""
    print("\n=== Checkpointer 全量缓冲记忆 ===")

    agent = build_agent_with_memory()
    thread_id = "user_001"

    conversations = [
        "我叫小明，我喜欢编程。",
        "我最喜欢的语言是 Python。",
        "我刚才说我叫什么？我喜欢什么？",
    ]

    for msg in conversations:
        response = chat(agent, msg, thread_id)
        print(f"User: {msg}")
        print(f"AI:   {response}\n")

    history = get_thread_messages(agent, thread_id)
    print(f"对话历史共 {len(history)} 条消息 (来自 checkpointer.get_state)")


# ========== 3. Demo: 多会话隔离 ==========

def demo_multi_thread():
    """不同 thread_id 互不干扰"""
    print("\n=== 多会话隔离 (thread_id) ===")

    agent = build_agent_with_memory(temperature=0.3)

    chat(agent, "我叫 Alice，我是设计师。", thread_id="alice")
    chat(agent, "我叫 Bob，我是后端工程师。", thread_id="bob")

    alice_reply = chat(agent, "我叫什么？职业是什么？", thread_id="alice")
    bob_reply = chat(agent, "我叫什么？职业是什么？", thread_id="bob")

    print(f"Alice 会话: {alice_reply}")
    print(f"Bob 会话:   {bob_reply}")


# ========== 4. Demo: 摘要记忆闭环 (get_state → 摘要 → update_state) ==========

def demo_summary_checkpoint():
    """真实 Agent 对话 → 摘要 → 写回 checkpointer → 验证记忆"""
    print("\n=== 摘要记忆闭环 (checkpointer) ===")

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    agent = build_agent_with_memory(temperature=0.3)
    thread_id = "summary_demo"

    seed_turns = [
        "你好，我叫张三，在北京工作。",
        "我主要用 Python 做后端开发。",
        "最近在学 LangChain 和 LangGraph。",
    ]
    for t in seed_turns:
        chat(agent, t, thread_id)

    messages = get_thread_messages(agent, thread_id)
    print(f"摘要前消息数: {len(messages)}")

    summarizer = init_chat_model("openai:gpt-4o-mini", temperature=0)
    summary_prompt = ChatPromptTemplate.from_messages([
        ("system", "将以下对话总结为一句话（保留姓名、地点、技术栈等关键事实）:"),
        ("human", "{conversation}"),
    ])
    conversation_text = "\n".join(
        f"{'用户' if isinstance(m, HumanMessage) else 'AI'}: {m.content}"
        for m in messages
        if getattr(m, "content", None)
    )
    summary = (summary_prompt | summarizer | StrOutputParser()).invoke(
        {"conversation": conversation_text}
    )
    print(f"生成摘要: {summary}")

    replace_thread_messages(
        agent,
        thread_id,
        [SystemMessage(content=f"[此前对话摘要] {summary}")],
    )
    print(f"写回后消息数: {len(get_thread_messages(agent, thread_id))}")

    reply = chat(agent, "我叫什么？在哪里工作？学什么？", thread_id)
    print(f"摘要后回忆: {reply}")


# ========== 5. Demo: trim + update_state 写回 ==========

def demo_update_state():
    """get_state → trim_messages → update_state → 继续对话"""
    print("\n=== update_state 裁剪历史 ===")

    agent = build_agent_with_memory(temperature=0.3)
    thread_id = "trim_demo"

    rounds = [
        "第1轮：记住代号 ALPHA。",
        "第2轮：记住代号 BETA。",
        "第3轮：记住代号 GAMMA。",
        "第4轮：记住代号 DELTA。",
        "第5轮：记住代号 EPSILON。",
        "第6轮：我最后一个代号是什么？",
    ]
    for r in rounds[:-1]:
        chat(agent, r, thread_id)

    before = len(get_thread_messages(agent, thread_id))
    b, a = trim_and_persist(agent, thread_id, max_tokens=80)
    print(f"裁剪: {b} 条 → {a} 条")

    reply = chat(agent, rounds[-1], thread_id)
    print(f"裁剪后回答: {reply}")
    print("(较早轮次可能已被裁掉，仅保留最近上下文)")


# ========== 6. Demo: 智能消息裁剪（静态示例） ==========

def demo_trim_messages():
    """trim_messages 工具演示（与 05 相同数据）"""
    print("\n=== 智能消息裁剪 (trim_messages) ===")

    messages = [
        SystemMessage(content="你是一个助手。"),
        HumanMessage(content="第1轮: 你叫什么？"),
        AIMessage(content="第1轮: 我叫 AI 助手。"),
        HumanMessage(content="第2轮: 今天天气如何？"),
        AIMessage(content="第2轮: 抱歉我无法获取实时天气数据。"),
        HumanMessage(content="第3轮: 帮我查一下股票？"),
        AIMessage(content="第3轮: 建议使用专业的金融数据 API。"),
        HumanMessage(content="第4轮: Python 怎么读取 CSV？"),
        AIMessage(content="第4轮: 使用 pandas.read_csv() 即可。"),
        HumanMessage(content="第5轮: 那如何写入呢？"),
    ]

    trimmed = trim_messages(
        messages,
        max_tokens=100,
        strategy="last",
        token_counter=len,
        include_system=True,
        allow_partial=False,
        start_on="human",
    )

    print(f"原始消息数: {len(messages)}")
    print(f"裁剪后消息数: {len(trimmed)}")
    for msg in trimmed:
        print(f"  [{type(msg).__name__}]: {msg.content}")


# ========== 7. Demo: SqliteSaver 跨进程持久化 ==========

def demo_sqlite_persistence():
    """SqliteSaver: 模拟进程重启后同 thread_id 恢复会话"""
    print("\n=== SqliteSaver 持久化 ===")

    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
    except ImportError:
        print("  (跳过: pip install langgraph-checkpoint-sqlite)")
        return

    db_path = os.path.join(tempfile.gettempdir(), "learn_10_checkpoint.sqlite")
    conn = f"sqlite:///{db_path}"
    thread_id = "persist_user"

    print(f"  数据库: {db_path}")

    with SqliteSaver.from_conn_string(conn) as checkpointer:
        agent = build_agent_with_memory(checkpointer=checkpointer, temperature=0.3)
        chat(agent, "记住：我的幸运数字是 42。", thread_id)
        print("  [进程 A] 已写入: 幸运数字 42")

    with SqliteSaver.from_conn_string(conn) as checkpointer:
        agent = build_agent_with_memory(checkpointer=checkpointer, temperature=0.3)
        reply = chat(agent, "我的幸运数字是多少？只回答数字。", thread_id)
        print(f"  [进程 B 重启] 回忆: {reply}")


# ========== 8. Demo: 检查 Checkpointer 状态 ==========

def demo_inspect_state():
    """get_state 查看持久化状态"""
    print("\n=== 检查 Checkpointer 状态 ===")

    agent = build_agent_with_memory(temperature=0.5)
    thread_id = "inspect_demo"

    chat(agent, "记住：我的宠物是一只叫豆豆的柯基。", thread_id)
    chat(agent, "我的宠物叫什么？什么品种？", thread_id)

    state = agent.get_state(config=thread_config(thread_id))
    if state:
        print(f"  next 节点: {state.next}")
        cfg = state.config.get("configurable", {})
        print(f"  checkpoint_id: {cfg.get('checkpoint_id', 'N/A')}")
        msgs = state.values.get("messages", []) if state.values else []
        print(f"  消息列表 ({len(msgs)} 条):")
        for i, m in enumerate(msgs):
            role = type(m).__name__
            preview = (m.content[:50] + "...") if len(m.content) > 50 else m.content
            print(f"    [{i}] {role}: {preview}")


if __name__ == "__main__":
    print("=" * 60)
    print("10 - Checkpointer: v1 对话记忆系统")
    print("=" * 60)

    demo_buffer_memory()
    demo_multi_thread()
    demo_summary_checkpoint()
    demo_update_state()
    demo_trim_messages()
    demo_sqlite_persistence()
    demo_inspect_state()

    print("\n" + "=" * 60)
    print("05_memory.py vs 10_check_pointer.py")
    print("=" * 60)
    print("| 05 (Chain)                    | 10 (Agent v1)                |")
    print("|-------------------------------|------------------------------|")
    print("| InMemoryChatMessageHistory    | InMemorySaver / SqliteSaver  |")
    print("| session_id                    | thread_id                    |")
    print("| RunnableWithMessageHistory    | create_agent(checkpointer=)  |")
    print("| get_session_history()         | agent.get_state()            |")
    print("| 手动 store 字典               | agent.update_state() 写回    |")
    print("\n核心要点:")
    print("1. checkpointer 在每次 invoke 后自动保存 Agent 状态")
    print("2. thread_id 隔离会话；SqliteSaver 支持重启后恢复")
    print("3. update_state + RemoveMessage(REMOVE_ALL_MESSAGES) 可替换历史")
    print("4. 带记忆 token 流见 11_stream_memory.py")
    print("5. 结构化输出见 12_structured_output.py；综合 Agent 见 09_agent_final.py")
