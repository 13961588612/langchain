"""
04_chains_lcel.py - LCEL (LangChain Expression Language)

学习要点:
1. LCEL 的 `|` 管道操作符: 串联组件
2. RunnableSequence: 顺序执行
3. RunnableParallel: 并行执行多个分支
4. RunnablePassthrough: 透传数据
5. RunnableLambda: 插入自定义函数
6. .with_config() / .with_fallbacks(): 配置与容错
"""
import time
from dotenv import load_dotenv

load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableParallel,
    RunnableLambda,
    RunnableSequence,
    RunnableConfig,
)
from langchain.messages import HumanMessage


def demo_basic_chain():
    """最基础的 LCEL Chain: Prompt | Model | OutputParser"""
    print("\n=== 基础 LCEL Chain ===")

    prompt = ChatPromptTemplate.from_template(
        "将以下文本翻译成{language}:\n\n{text}"
    )
    model = init_chat_model("openai:gpt-4o", temperature=0.3)
    parser = StrOutputParser()

    # LCEL 管道链
    chain = prompt | model | parser

    result = chain.invoke({
        "language": "日语",
        "text": "人工智能正在改变我们的生活方式。"
    })

    print(f"翻译结果: {result}")


def demo_runnable_parallel():
    """RunnableParallel: 同时执行多个分析维度"""
    print("\n=== RunnableParallel 并行分析 ===")

    model = init_chat_model("openai:gpt-4o", temperature=0.3)

    # 三个并行的分析维度
    sentiment_prompt = ChatPromptTemplate.from_template(
        "分析以下文本的情感（正面/负面/中性）:\n{text}"
    )
    summary_prompt = ChatPromptTemplate.from_template(
        "用一句话总结以下文本:\n{text}"
    )
    keywords_prompt = ChatPromptTemplate.from_template(
        "提取以下文本的3个关键词，用逗号分隔:\n{text}"
    )

    parallel_chain = RunnableParallel(
        sentiment=sentiment_prompt | model | StrOutputParser(),
        summary=summary_prompt | model | StrOutputParser(),
        keywords=keywords_prompt | model | StrOutputParser(),
    )

    text = """
    LangChain 是一个强大的 LLM 应用开发框架，它提供了 Chain、Agent、
    Tool 等核心抽象，让开发者可以快速构建复杂的 AI 应用。
    无论是简单的问答系统还是多步骤的智能体工作流，LangChain 都能胜任。
    """

    start = time.time()
    result = parallel_chain.invoke({"text": text})
    elapsed = time.time() - start

    print(f"[{elapsed:.2f}s] 情感: {result['sentiment'].strip()}")
    print(f"[{elapsed:.2f}s] 总结: {result['summary'].strip()}")
    print(f"[{elapsed:.2f}s] 关键词: {result['keywords'].strip()}")
    print("  (三个分析是并行执行的, 总时间约等于最慢的那个)")


def demo_passthrough():
    """RunnablePassthrough: 透传与数据装配"""
    print("\n=== RunnablePassthrough 数据透传 ===")

    prompt = ChatPromptTemplate.from_template(
        "根据以下信息写一段人物简介:\n"
        "姓名: {name}\n职业: {job}\n原始资料: {source}"
    )
    model = init_chat_model("openai:gpt-4o", temperature=0.7)

    # RunnablePassthrough 用于透传数据同时添加新字段
    chain = (
        RunnablePassthrough.assign(
            job=lambda x: x["job"].upper(),
            source=lambda x: f"来源: {x['source']}",
        )
        | prompt
        | model
        | StrOutputParser()
    )

    result = chain.invoke({
        "name": "张三",
        "job": "软件工程师",
        "source": "LinkedIn 个人资料",
    })
    print(result)


def demo_lambda_in_chain():
    """在 Chain 中插入自定义 Python 函数"""
    print("\n=== RunnableLambda 自定义函数 ===")

    model = init_chat_model("openai:gpt-4o", temperature=0)

    def normalize_text(text: str) -> str:
        """预处理: 去除多余空白和统一标点"""
        import re
        text = re.sub(r"\s+", " ", text)
        text = text.replace("！", "!").replace("？", "?")
        return text.strip()

    def add_header(text: str) -> str:
        """后处理: 添加格式化标题"""
        return f"## 分析结果\n\n{text}"

    prompt = ChatPromptTemplate.from_template(
        "请分类以下文本的主题:\n{text}"
    )

    chain = (
        RunnableLambda(normalize_text)
        | prompt
        | model
        | StrOutputParser()
        | RunnableLambda(add_header)
    )

    result = chain.invoke({
        "text": "  人工智能   正在   改变   世界！！     这是一个  令人兴奋的  时代？？   "
    })
    print(result)


def demo_config_and_fallback():
    """链的配置和容错回退"""
    print("\n=== 配置与回退 ===")

    prompt = ChatPromptTemplate.from_template(
        "用一句话解释: {concept}"
    )

    # 主模型
    primary_model = init_chat_model("openai:gpt-4o", temperature=0.5)

    # 回退模型（如果主模型失败）
    try:
        fallback_model = init_chat_model("google_genai:gemini-2.5-flash", temperature=0.5)

        chain = prompt | primary_model.with_fallbacks([fallback_model]) | StrOutputParser()
    except Exception:
        # 如果 Gemini 不可用，只用主模型
        chain = prompt | primary_model | StrOutputParser()

    # with_config 设置运行参数
    result = chain.with_config(
        configurable={"llm_temperature": 0.3},
        tags=["explanation", "single-sentence"],
        metadata={"concept": "RAG"},
    ).invoke({"concept": "RAG（检索增强生成）"})

    print(result)
    print("\n  .with_fallbacks() 在主模型失败时自动切换到备用模型")
    print("  .with_config() 可为链设置 tags/metadata/可配置参数")


if __name__ == "__main__":
    print("=" * 60)
    print("04 - LCEL: LangChain Expression Language")
    print("=" * 60)

    demo_basic_chain()
    demo_runnable_parallel()
    demo_passthrough()
    demo_lambda_in_chain()
    demo_config_and_fallback()

    print("\n核心要点:")
    print("1. `|` 管道操作符连接组件: prompt | model | parser")
    print("2. RunnableParallel 并行执行多个分支（自动并发）")
    print("3. RunnablePassthrough.assign() 在透传数据时添加字段")
    print("4. RunnableLambda 在链中插入任意 Python 函数")
    print("5. .with_fallbacks() 配置容错回退链")
    print("6. .with_config() 为链附加 tags/metadata 用于追踪")
