"""
08_streaming.py - 流式输出

学习要点:
1. .stream(): 同步流式输出
2. .astream(): 异步流式输出
3. .astream_events(): 事件级流式（最细粒度）
4. 不同 stream_mode: values / updates / messages / custom / debug
5. Streaming 在 UI 中的实际应用
"""
import asyncio
from dotenv import load_dotenv

load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.messages import HumanMessage


def demo_sync_stream():
    """同步流式: .stream()"""
    print("\n=== 同步流式 (.stream) ===")

    model = init_chat_model("openai:gpt-4o", temperature=0.7)
    prompt = ChatPromptTemplate.from_template(
        "请用中文写一首关于编程的短诗（4行即可）。"
    )

    chain = prompt | model | StrOutputParser()

    print("流式输出:")
    for chunk in chain.stream({}):
        print(chunk, end="", flush=True)
    print("\n")


async def demo_async_stream():
    """异步流式: .astream()"""
    print("\n=== 异步流式 (.astream) ===")

    model = init_chat_model("openai:gpt-4o", temperature=0.7)
    prompt = ChatPromptTemplate.from_template(
        "列举3个学习 LangChain 的小技巧，每个一句话。"
    )

    chain = prompt | model | StrOutputParser()

    print("异步流式输出:")
    async for chunk in chain.astream({}):
        print(chunk, end="", flush=True)
    print("\n")


async def demo_astream_events():
    """事件级流式: .astream_events() - 最细粒度"""
    print("\n=== 事件级流式 (.astream_events) ===")

    from langchain_core.tools import tool

    @tool
    def calculator(expression: str) -> str:
        """计算数学表达式"""
        return f"计算结果: {eval(expression)}"

    model = init_chat_model("openai:gpt-4o", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个助手，必要时应使用计算器工具。"),
        ("human", "{question}"),
    ])

    chain = prompt | model.bind_tools([calculator])

    print("事件级流式输出:")
    async for event in chain.astream_events(
        {"question": "123 * 456 等于多少？"},
        version="v2",
    ):
        kind = event.get("event", "")

        if kind == "on_chat_model_stream":
            # Token 级别的内容
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                print(chunk.content, end="", flush=True)

        elif kind == "on_tool_start":
            print(f"\n[🔧 调用工具: {event.get('name')}]")

        elif kind == "on_tool_end":
            output = event.get("data", {}).get("output", "")
            print(f"[✅ 工具返回: {output}]")

    print("\n")


def demo_compare_modes():
    """对比 stream_mode 的不同模式"""
    print("\n=== stream_mode 对比 ===")

    model = init_chat_model("openai:gpt-4o", temperature=0)
    prompt = ChatPromptTemplate.from_template(
        "简单回复: 1+1=?"
    )
    chain = prompt | model

    print("\nstream_mode='values' (完整状态快照):")
    for chunk in chain.stream({}, stream_mode="values"):
        if isinstance(chunk, dict) and "messages" in chunk:
            content = chunk["messages"][-1].content if chunk["messages"] else ""
            print(f"  [values] {content}")

    print("\nstream_mode='updates' (增量更新):")
    for chunk in chain.stream({}, stream_mode="updates"):
        print(f"  [updates] {chunk}")

    print("\nstream_mode='messages' (消息+元数据):")
    for chunk in chain.stream({}, stream_mode="messages"):
        if isinstance(chunk, tuple) and len(chunk) == 2:
            msg = chunk[0]
            metadata = chunk[1]
            print(f"  [messages] {type(msg).__name__}: {msg.content} | meta: {dict(metadata)}")


if __name__ == "__main__":
    print("=" * 60)
    print("08 - Streaming: 流式输出")
    print("=" * 60)

    # 同步流式
    demo_sync_stream()

    # 异步流式
    asyncio.run(demo_async_stream())

    # 事件级流式（最细粒度）
    asyncio.run(demo_astream_events())

    # 对比 stream_mode
    demo_compare_modes()

    print("\n核心要点:")
    print("1. .stream() 逐 token 输出，适合实时 UI 展示")
    print("2. .astream() 异步版本，适合 WebSocket / SSE 场景")
    print("3. .astream_events(version='v2') 最细粒度，可捕获 token/工具调用/链事件")
    print("4. stream_mode='values': 每个节点后的完整状态快照")
    print("5. stream_mode='updates': 每个节点的增量更新")
    print("6. stream_mode='messages': 消息流 + 元数据 (token 级)")
    print("7. stream_mode='custom': 自定义流式数据")
    print("8. stream_mode='debug': 调试信息")
    print("9. Agent 场景推荐 stream_mode='updates' 获取每步执行结果")
