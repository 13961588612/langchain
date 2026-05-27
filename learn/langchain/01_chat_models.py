"""
01_chat_models.py - 多 Provider 模型切换与基本对话

学习要点:
1. 使用 init_chat_model 统一接口切换不同模型
2. 理解 BaseChatModel 的核心方法: invoke / ainvoke
3. 如何安全地加载环境变量中的 API Key
"""
import os
from dotenv import load_dotenv

load_dotenv()

from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


def demo_openai():
    """演示 OpenAI 模型调用"""
    print("\n=== OpenAI GPT-4o ===")
    model = init_chat_model("openai:gpt-4o", temperature=0.7)
    response = model.invoke([
        SystemMessage(content="你是一个简洁的助手，用中文回答。"),
        HumanMessage(content="用一句话解释什么是 LangChain？"),
    ])
    print(f"回复: {response.content}")
    print(f"Token 用量: {response.usage_metadata}")


def demo_anthropic():
    """演示 Anthropic Claude 模型调用"""
    print("\n=== Anthropic Claude ===")
    try:
        model = init_chat_model("anthropic:claude-sonnet-4-20250514", temperature=0.5)
        response = model.invoke([
            SystemMessage(content="你是一个简洁的助手，用中文回答。"),
            HumanMessage(content="用一句话解释什么是 LangChain？"),
        ])
        print(f"回复: {response.content}")
    except Exception as e:
        print(f"Anthropic 调用失败（可能未配置 API Key）: {e}")


def demo_google():
    """演示 Google Gemini 模型调用"""
    print("\n=== Google Gemini ===")
    try:
        model = init_chat_model("google_genai:gemini-2.5-flash", temperature=0.7)
        response = model.invoke([
            SystemMessage(content="你是一个简洁的助手，用中文回答。"),
            HumanMessage(content="用一句话解释什么是 LangChain？"),
        ])
        print(f"回复: {response.content}")
    except Exception as e:
        print(f"Google 调用失败（可能未配置 API Key）: {e}")


def demo_ollama():
    """演示本地 Ollama 模型调用"""
    print("\n=== Ollama (本地) ===")
    try:
        model = init_chat_model("ollama:llama3.2", temperature=0.7)
        response = model.invoke([
            SystemMessage(content="你是一个简洁的助手，用中文回答。"),
            HumanMessage(content="用一句话解释什么是 LangChain？"),
        ])
        print(f"回复: {response.content}")
    except Exception as e:
        print(f"Ollama 调用失败（可能未运行 Ollama 服务）: {e}")


def demo_deepseek_v4():
    """演示 DeepSeek v4 模型调用

    DeepSeek v4 支持深度思考 (Deep Thinking) 模式:
    - deepseek-v4-pro: 完整版，复杂推理场景
    - deepseek-v4-flash: 轻量版，快速响应
    """
    print("\n=== DeepSeek v4 ===")
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key or api_key == "sk-xxx":
        print("跳过: 未配置 DEEPSEEK_API_KEY")
        return

    try:
        # 方式1: 通过 init_chat_model (需安装 langchain-deepseek)
        model = init_chat_model(
            "deepseek:deepseek-v4-pro",
            temperature=0.5,
        )
        response = model.invoke([
            SystemMessage(content="你是一个简洁的助手，用中文回答。"),
            HumanMessage(content="用一句话解释什么是 LangChain？"),
        ])
        print(f"回复: {response.content}")
    except ImportError:
        print("方式1 不可用 (需 pip install langchain-deepseek)")
        # 方式2: 通过 OpenAI 兼容接口
        try:
            model = ChatOpenAI(
                model="deepseek-v4-pro",
                base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                api_key=api_key,
                temperature=0.5,
            )
            response = model.invoke([
                SystemMessage(content="你是一个简洁的助手，用中文回答。"),
                HumanMessage(content="用一句话解释什么是 LangChain？"),
            ])
            print(f"回复 (兼容接口): {response.content}")
        except Exception as e:
            print(f"DeepSeek 调用失败: {e}")
    except Exception as e:
        print(f"DeepSeek 调用失败: {e}")


def demo_qwen():
    """演示阿里云 Qwen 模型调用

    注意: init_chat_model 暂未原生支持 Qwen (GitHub #34183)，
    此处使用 ChatOpenAI + OpenAI 兼容接口 (DashScope) 调用
    """
    print("\n=== Qwen (阿里云百炼) ===")
    api_key = os.getenv("QWEN_API_KEY")
    if not api_key or api_key == "sk-xxx":
        print("跳过: 未配置 QWEN_API_KEY")
        return

    try:
        model = ChatOpenAI(
            model="qwen3.6-plus",  # qwen-turbo / qwen-plus / qwen-max
            base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            api_key=api_key,
            temperature=0.7,
        )
        response = model.invoke([
            SystemMessage(content="你是一个简洁的助手，用中文回答。"),
            HumanMessage(content="用一句话解释什么是 LangChain？"),
        ])
        print(f"回复: {response.content}")
    except Exception as e:
        print(f"Qwen 调用失败: {e}")


def demo_provider_comparison():
    """
    趣味对比: 让不同模型回答同一个问题并比较结果
    实际项目中, init_chat_model 让你只需切换字符串即可换模型
    """
    print("\n=== 多模型对比: '什么是智能体(Agent)?' ===")
    question = "用一句话解释什么是 AI 智能体(Agent)？"

    providers = []
    # 仅测试已配置 API Key 的 provider
    if os.getenv("OPENAI_API_KEY"):
        providers.append("openai:gpt-4o")
    if os.getenv("ANTHROPIC_API_KEY"):
        providers.append("anthropic:claude-sonnet-4-20250514")
    if os.getenv("GOOGLE_API_KEY"):
        providers.append("google_genai:gemini-2.5-flash")
    if os.getenv("DEEPSEEK_API_KEY") and os.getenv("DEEPSEEK_API_KEY") != "sk-xxx":
        providers.append("deepseek:deepseek-v4-pro")
    if os.getenv("QWEN_API_KEY") and os.getenv("QWEN_API_KEY") != "sk-xxx":
        providers.append("qwen")

    for provider_model in providers:
        try:
            if provider_model == "qwen":
                model = ChatOpenAI(
                    model="qwen-plus",
                    base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
                    api_key=os.getenv("QWEN_API_KEY"),
                    temperature=0.3,
                )
            else:
                model = init_chat_model(provider_model, temperature=0.3)
            response = model.invoke([HumanMessage(content=question)])
            print(f"[{provider_model}]: {response.content[:100]}...")
        except Exception as e:
            print(f"[{provider_model}]: 失败 - {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("01 - Chat Models: 多 Provider 模型切换")
    print("=" * 60)

    # 切换模型只需要改 provider:model 字符串
    #demo_openai()        # OpenAI
    #demo_anthropic()     # Anthropic Claude
    #demo_google()        # Google Gemini
    #demo_ollama()        # 本地 Ollama
    demo_deepseek_v4()   # DeepSeek v4
    demo_qwen()          # 阿里云 Qwen

    demo_provider_comparison()

    print("\n核心要点:")
    print("1. init_chat_model('provider:model') 统一所有模型的创建接口")
    print("2. 使用 SystemMessage + HumanMessage 构建对话")
    print("3. invoke() 方法发送消息并获取完整回复")
    print("4. 不同 Provider 的模型支持通过 model_kwargs 传入特有参数")
    print("5. init_chat_model 原生支持 DeepSeek，Qwen 通过 ChatOpenAI + 兼容接口")
    print("6. DeepSeek v4: deepseek-v4-pro / deepseek-v4-flash")
