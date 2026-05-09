"""
07_callbacks.py - 回调系统与 LangSmith 追踪

学习要点:
1. BaseCallbackHandler: 自定义回调处理器
2. 标准回调事件: on_llm_start / on_llm_end / on_tool_start / on_chain_start
3. LangSmith 追踪: 自动记录所有链和模型调用
4. 回调在调试和监控中的实际应用
"""
import os
import time
from typing import Any
from dotenv import load_dotenv

load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.callbacks import BaseCallbackHandler
from langchain_core.callbacks import CallbackManager
from langchain.tools import tool
from langchain.messages import HumanMessage
from langchain_core.runnables import RunnableLambda


# ========== 1. 自定义回调处理器 ==========

class TimingCallback(BaseCallbackHandler):
    """记录每个步骤耗时的回调"""

    def __init__(self):
        self.timers: dict[str, float] = {}
        self.events: list[dict] = []

    def on_llm_start(self, serialized, prompts, **kwargs):
        run_id = str(kwargs.get("run_id", ""))
        self.timers[run_id] = time.time()
        self.events.append({"type": "llm_start", "run_id": run_id[:8]})

    def on_llm_end(self, response, **kwargs):
        run_id = str(kwargs.get("run_id", ""))
        elapsed = time.time() - self.timers.pop(run_id, time.time())
        self.events.append({"type": "llm_end", "run_id": run_id[:8], "elapsed": f"{elapsed:.2f}s"})

    def on_chain_start(self, serialized, inputs, **kwargs):
        self.events.append({"type": "chain_start", "name": serialized.get("name", "unknown")})

    def on_chain_end(self, outputs, **kwargs):
        self.events.append({"type": "chain_end"})

    def on_tool_start(self, serialized, input_str, **kwargs):
        self.events.append({"type": "tool_start", "name": serialized.get("name", "unknown")})

    def on_tool_end(self, output, **kwargs):
        self.events.append({"type": "tool_end"})


class TokenCounterCallback(BaseCallbackHandler):
    """Token 计数回调"""

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.llm_calls = 0

    def on_llm_end(self, response, **kwargs):
        self.llm_calls += 1
        if hasattr(response, "llm_output") and response.llm_output:
            usage = response.llm_output.get("token_usage", {})
            self.total_input_tokens += usage.get("prompt_tokens", 0)
            self.total_output_tokens += usage.get("completion_tokens", 0)

        # 另一种方式: 通过 generations
        if hasattr(response, "generations"):
            for gen_list in response.generations:
                for gen in gen_list:
                    if hasattr(gen, "generation_info"):
                        usage = gen.generation_info.get("usage_metadata", {})
                        self.total_input_tokens += usage.get("input_tokens", 0)
                        self.total_output_tokens += usage.get("output_tokens", 0)


def demo_custom_callback():
    """演示自定义回调"""
    print("\n=== 自定义回调: 耗时追踪 + Token 计数 ===")

    timing_cb = TimingCallback()
    token_cb = TokenCounterCallback()

    # 创建带回调的管理器
    callback_manager = CallbackManager([timing_cb, token_cb])

    model = init_chat_model(
        "openai:gpt-4o",
        temperature=0.7,
        callbacks=callback_manager,
    )

    @tool
    def get_time() -> str:
        """获取当前时间"""
        return time.strftime("%H:%M:%S")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个简洁的助手。"),
        ("human", "{question}"),
    ])

    chain = prompt | model.bind_tools([get_time]) | StrOutputParser()

    result = chain.invoke(
        {"question": "现在几点了？帮我用中文回答。"},
        config={"callbacks": callback_manager},
    )

    print(f"回复: {result}")
    print(f"\n事件时间线:")
    for event in timing_cb.events:
        extra = f" ({event.get('elapsed', '')})" if 'elapsed' in event else ""
        print(f"  [{event['type']}] {event.get('name', event.get('run_id', ''))}{extra}")

    print(f"\nToken 统计:")
    print(f"  LLM 调用次数: {token_cb.llm_calls}")
    print(f"  输入 Token: {token_cb.total_input_tokens}")
    print(f"  输出 Token: {token_cb.total_output_tokens}")


def demo_langsmith_tracing():
    """演示 LangSmith 追踪集成"""
    print("\n=== LangSmith 追踪 ===")

    langsmith_key = os.getenv("LANGSMITH_API_KEY")
    if not langsmith_key:
        print("(跳过: 未配置 LANGSMITH_API_KEY 环境变量)")
        print("获取免费 API Key: https://smith.langchain.com")
        print("配置后所有 LLM 调用、Chain、Tool 都会自动记录到 LangSmith")
        return

    # LangSmith 会自动追踪（如果环境变量已设置）
    os.environ["LANGSMITH_TRACING"] = "true"

    model = init_chat_model("openai:gpt-4o", temperature=0.5)
    prompt = ChatPromptTemplate.from_template(
        "用中文解释: {concept}"
    )
    chain = prompt | model | StrOutputParser()

    # 带 metadata 和 tags 的调用
    result = chain.invoke(
        {"concept": "回调函数"},
        config={
            "metadata": {"user": "student", "lesson": "07_callbacks"},
            "tags": ["learning", "callbacks", "demo"],
            "run_name": "解释回调函数",
        },
    )
    print(f"回复: {result}")
    print(f"\n此调用已自动记录到 LangSmith 项目: {os.getenv('LANGSMITH_PROJECT', 'default')}")
    print("可以在 https://smith.langchain.com 查看调用链路、耗时、Token 用量")


if __name__ == "__main__":
    print("=" * 60)
    print("07 - Callbacks: 回调系统与追踪")
    print("=" * 60)

    demo_custom_callback()
    demo_langsmith_tracing()

    print("\n核心要点:")
    print("1. BaseCallbackHandler 支持 on_llm_start/end, on_tool_start/end, on_chain_start/end")
    print("2. CallbackManager 可组合多个回调处理器")
    print("3. 自定义回调可用于: 耗时追踪、Token 计数、日志记录、告警")
    print("4. LangSmith 是 LangChain 官方的全链路追踪平台（免费层可用）")
    print("5. 配置 LANGSMITH_API_KEY 后追踪自动生效，无需代码改动")
