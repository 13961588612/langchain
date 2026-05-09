"""
05_memory.py - 对话记忆系统

学习要点:
1. ConversationBufferMemory: 简单的全量记忆
2. ConversationSummaryMemory: 摘要压缩记忆
3. RunnableWithMessageHistory: 自动管理对话历史
4. trim_messages: 智能裁剪超长对话
5. 记忆 vs 上下文窗口: 何时用何种策略
"""
from dotenv import load_dotenv

load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.messages import HumanMessage, AIMessage, SystemMessage, trim_messages
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.language_models import BaseChatModel


# ========== 1. 内存中的对话历史存储 ==========

store: dict[str, InMemoryChatMessageHistory] = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """获取或创建会话历史（生产环境应使用数据库存储）"""
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


def demo_buffer_memory():
    """ConversationBufferMemory: 保存完整对话历史"""
    print("\n=== 全量缓冲记忆 ===")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个友好的助手。"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])
    model = init_chat_model("openai:gpt-4o", temperature=0.7)

    chain = prompt | model | StrOutputParser()

    # 用 RunnableWithMessageHistory 自动管理历史
    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )

    session_id = "user_001"
    conversations = [
        "我叫小明，我喜欢编程。",
        "我最喜欢的语言是 Python。",
        "我刚才说我叫什么？我喜欢什么？",
    ]

    for msg in conversations:
        response = chain_with_history.invoke(
            {"input": msg},
            config={"configurable": {"session_id": session_id}},
        )
        print(f"User: {msg}")
        print(f"AI:   {response}\n")

    # 查看当前对话历史
    history = get_session_history(session_id)
    print(f"对话历史共 {len(history.messages)} 条消息")


def demo_summary_memory():
    """ConversationSummaryMemory: 将历史对话压缩为摘要"""
    print("\n=== 摘要记忆 ===")

    model = init_chat_model("openai:gpt-4o", temperature=0.3)

    def summarize_history(messages: list) -> str:
        """将对话历史压缩为摘要"""
        if len(messages) <= 4:
            return "\n".join([f"{'用户' if isinstance(m, HumanMessage) else 'AI'}: {m.content}" for m in messages])

        summarizer = init_chat_model("openai:gpt-4o-mini", temperature=0)
        summary_prompt = ChatPromptTemplate.from_messages([
            ("system", "将以下对话总结为一句话摘要（保留关键信息如名字、偏好、事实）:"),
            ("human", "{conversation}"),
        ])
        conversation_text = "\n".join([m.content for m in messages])
        summary = (summary_prompt | summarizer | StrOutputParser()).invoke({"conversation": conversation_text})
        return f"[对话摘要] {summary}"

    # 模拟长对话
    messages = [
        HumanMessage(content="你好，我叫张三。"),
        AIMessage(content="你好张三！有什么我能帮你的吗？"),
        HumanMessage(content="我想了解 Python 的装饰器。"),
        AIMessage(content="装饰器是一种修改函数行为的语法糖..."),
        HumanMessage(content="能举个简单例子吗？"),
        AIMessage(content="当然！比如 @staticmethod 就是一个装饰器..."),
        HumanMessage(content="谢谢！我还有一个问题关于异步编程。"),
    ]

    summary = summarize_history(messages)
    print(f"原始消息数: {len(messages)}")
    print(f"摘要结果:\n{summary}")


def demo_trim_messages():
    """trim_messages: 智能裁剪超长对话，保留最近的 N 条 + 系统消息"""
    print("\n=== 智能消息裁剪 ===")

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

    # 保留最近 6 条消息 + 始终保留 system message
    trimmed = trim_messages(
        messages,
        max_tokens=100,          # 最大 token 数
        strategy="last",         # 保留最后的消息
        token_counter=len,       # 简化用字符数代替（生产用 tiktoken）
        include_system=True,     # 始终包含 system message
        allow_partial=False,
        start_on="human",        # 从 human message 开始（确保对话完整性）
    )

    print(f"原始消息数: {len(messages)}")
    print(f"裁剪后消息数: {len(trimmed)}")
    for msg in trimmed:
        print(f"  [{type(msg).__name__}]: {msg.content}")


if __name__ == "__main__":
    print("=" * 60)
    print("05 - Memory: 对话记忆系统")
    print("=" * 60)

    demo_buffer_memory()
    demo_summary_memory()
    demo_trim_messages()

    print("\n核心要点:")
    print("1. RunnableWithMessageHistory 自动管理对话历史")
    print("2. 全量记忆适合短对话，长对话需用摘要或滑动窗口")
    print("3. trim_messages 按 token 数智能裁剪历史消息")
    print("4. 生产环境中历史存储应使用数据库而非内存字典")
    print("5. 摘要记忆用更便宜的模型生成摘要，节省 token 成本")
