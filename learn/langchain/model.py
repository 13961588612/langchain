"""
model.py - 统一模型工厂函数

提供 getModel(temperature) 函数，返回配置好的 DeepSeek 聊天模型实例。
"""

import os
from dotenv import load_dotenv

load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI


def getModel(temperature: float = 0.7):
    """获取 DeepSeek 聊天模型实例

    Args:
        temperature: 温度参数 (0.0-2.0)，越高越随机，越低越确定。
                     默认 0.7。

    Returns:
        BaseChatModel 实例，可直接调用 .invoke() / .stream() / .ainvoke()

    Raises:
        ValueError: 未配置 DEEPSEEK_API_KEY 时抛出

    Example:
        model = getModel(temperature=0.3)
        response = model.invoke("你好")
        print(response.content)
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    if not api_key:
        raise ValueError(
            "请在 .env 文件中配置 DEEPSEEK_API_KEY\n"
            "示例: DEEPSEEK_API_KEY=sk-xxxx"
        )

    # 方式1: 通过 langchain-deepseek 官方集成包
    try:
        from langchain_deepseek import ChatDeepSeek

        return ChatDeepSeek(
            model="deepseek-chat",
            api_key=api_key,
            temperature=temperature,
        )  # type: ignore[no-any-return]
    except ImportError:
        pass

    # 方式2: 通过 init_chat_model（需 langchain-deepseek 已安装）
    try:
        return init_chat_model(
            "deepseek:deepseek-chat",
            temperature=temperature,
        )  # type: ignore[no-any-return]
    except (ImportError, Exception):
        pass

    # 方式3: 通过 OpenAI 兼容接口（无需额外包，推荐用这个）
    return ChatOpenAI(
        model="deepseek-chat",
        base_url=base_url + "/v1" if not base_url.endswith("/v1") else base_url,
        api_key=api_key,
        temperature=temperature,
    )
