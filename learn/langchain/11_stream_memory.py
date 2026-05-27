"""
11_stream_memory.py - 带记忆的 Token 级流式输出

学习要点:
1. stream_mode='messages': Agent 逐 token 输出，适合聊天 UI
2. thread_id + checkpointer: 流式多轮对话仍保留上下文
3. stream_mode='updates': 按节点增量（工具调用、模型步）
4. 组合 stream_mode=['messages', 'updates'] 同时观察 token 与步骤
5. 与 08_streaming.py 对比: 08 是 Chain；本课是 Agent + 记忆

前置: 10_check_pointer.py（checkpointer / thread_id）
"""
import asyncio
from dotenv import load_dotenv

load_dotenv()

from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import AIMessageChunk


def build_streaming_agent(model_name: str = "openai:gpt-4o", temperature: float = 0.7):
    model = init_chat_model(model_name, temperature=temperature)
    return create_agent(
        model=model,
        tools=[],
        system_prompt="你是一个友好的助手，用中文简洁回答。",
        checkpointer=InMemorySaver(),
    )


def thread_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def stream_tokens(agent, user_input: str, thread_id: str) -> str:
    """stream_mode='messages' — 逐 token 打印，返回完整回复"""
    print(f"\n用户: {user_input}")
    print("助手: ", end="", flush=True)

    collected: list[str] = []
    for chunk, _metadata in agent.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config=thread_config(thread_id),
        stream_mode="messages",
    ):
        if isinstance(chunk, AIMessageChunk) and chunk.content:
            text = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
            print(text, end="", flush=True)
            collected.append(text)

    print()
    return "".join(collected)


def stream_with_updates(agent, user_input: str, thread_id: str) -> str:
    """stream_mode='updates' — 展示节点级增量（09 同款，带记忆）"""
    print(f"\n用户: {user_input}")
    final = ""

    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config=thread_config(thread_id),
        stream_mode="updates",
    ):
        for node_name, update in chunk.items():
            if node_name != "model":
                continue
            for msg in update.get("messages", []):
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        print(f"  [工具] {tc['name']}({tc.get('args', {})})")
                elif hasattr(msg, "content") and msg.content:
                    final = msg.content
                    print(f"  [model] {final[:80]}{'...' if len(final) > 80 else ''}")

    return final


async def astream_tokens(agent, user_input: str, thread_id: str) -> str:
    """异步 token 流 — WebSocket / SSE 场景"""
    print(f"\n[async] 用户: {user_input}")
    print("[async] 助手: ", end="", flush=True)

    collected: list[str] = []
    async for chunk, _metadata in agent.astream(
        {"messages": [{"role": "user", "content": user_input}]},
        config=thread_config(thread_id),
        stream_mode="messages",
    ):
        if isinstance(chunk, AIMessageChunk) and chunk.content:
            text = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
            print(text, end="", flush=True)
            collected.append(text)

    print()
    return "".join(collected)


def demo_token_stream_with_memory():
    """多轮流式对话 + checkpointer：第二轮应记住第一轮信息"""
    print("\n=== 带记忆的 Token 流 (stream_mode='messages') ===")

    agent = build_streaming_agent()
    thread_id = "stream_memory_001"

    stream_tokens(agent, "我叫小李，正在学 LangChain。", thread_id)
    stream_tokens(agent, "用一句话介绍 LangChain 是什么。", thread_id)
    answer = stream_tokens(agent, "我叫什么？我在学什么？", thread_id)

    state = agent.get_state(config=thread_config(thread_id))
    n = len(state.values.get("messages", [])) if state and state.values else 0
    print(f"\ncheckpointer 已保存 {n} 条消息")
    print(f"记忆验证: {'小李' in answer or 'LangChain' in answer}")


def demo_updates_vs_messages():
    """对比 updates（节点级）与 messages（token 级）"""
    print("\n=== updates vs messages ===")

    agent = build_streaming_agent(temperature=0.3)
    thread_id = "stream_compare"
    question = "用三句话介绍 Python 的 list 和 tuple 区别。"

    print("\n--- stream_mode='updates' ---")
    stream_with_updates(agent, question, thread_id)

    print("\n--- stream_mode='messages' (token) ---")
    stream_tokens(agent, "同上问题，再简短回答一遍。", thread_id)


def demo_dual_stream_modes():
    """同时订阅 messages + updates（调试时有用）"""
    print("\n=== 组合流: ['messages', 'updates'] ===")

    agent = build_streaming_agent(temperature=0.5)
    thread_id = "dual_stream"

    print("用户: 写一句关于编程的励志语。")
    print("输出: ", end="", flush=True)

    for mode, chunk in agent.stream(
        {"messages": [{"role": "user", "content": "写一句关于编程的励志语。"}]},
        config=thread_config(thread_id),
        stream_mode=["messages", "updates"],
    ):
        if mode == "messages":
            msg, _meta = chunk
            if isinstance(msg, AIMessageChunk) and msg.content:
                text = msg.content if isinstance(msg.content, str) else str(msg.content)
                print(text, end="", flush=True)
        elif mode == "updates":
            for node, upd in chunk.items():
                if node == "model" and upd.get("messages"):
                    print(f"\n  [updates/{node}] 本步完成", flush=True)

    print("\n")


if __name__ == "__main__":
    print("=" * 60)
    print("11 - 带记忆的 Token 流式输出")
    print("=" * 60)

    demo_token_stream_with_memory()
    demo_updates_vs_messages()
    demo_dual_stream_modes()

    print("\n运行异步示例...")
    agent = build_streaming_agent()
    asyncio.run(astream_tokens(agent, "异步流式：说一个 Python 小技巧。", "async_stream"))

    print("\n核心要点:")
    print("1. Agent + checkpointer + stream_mode='messages' = 带记忆的逐 token UI")
    print("2. thread_id 不变则多轮流式共享同一会话状态")
    print("3. stream_mode='updates' 适合展示工具调用与 Agent 步骤")
    print("4. 生产 UI: SSE/WebSocket 推送 messages 流；后台用 SqliteSaver")
    print("5. Chain 级流式见 08_streaming.py；RAG+工具流式见 09_agent_final.py")
