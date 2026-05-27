"""
12_structured_output.py - 结构化输出

学习要点:
1. model.with_structured_output(): 在 Chain 中直接得到 Pydantic 对象
2. create_agent(response_format=...): Agent 返回 structured_response
3. Pydantic / TypedDict / JSON Schema 多种 schema 形式
4. ToolStrategy: 模型不支持原生结构化时的回退策略
5. 结构化输出 vs 自由文本: 何时用于 API、表单、数据抽取

前置: 01_chat_models.py, 03_tools.py
"""
from typing import Literal
from dotenv import load_dotenv

load_dotenv()

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate


# ========== Schema 定义 ==========

class ContactInfo(BaseModel):
    """联系人信息"""
    name: str = Field(description="姓名")
    email: str = Field(description="邮箱")
    phone: str = Field(description="电话")


class ProductReview(BaseModel):
    """商品评价分析"""
    rating: int | None = Field(default=None, ge=1, le=5, description="评分 1-5")
    sentiment: Literal["positive", "negative"] = Field(description="情感倾向")
    key_points: list[str] = Field(description="关键词，每条 1-3 个词")


class MovieInfo(TypedDict):
    """电影信息 (TypedDict)"""
    title: str
    year: int
    genre: str


# ========== 1. Model 级结构化输出 (Chain 场景) ==========

def demo_model_structured_output():
    """init_chat_model + with_structured_output — 适合 LCEL 管道"""
    print("\n=== Model.with_structured_output (Pydantic) ===")

    model = init_chat_model("openai:gpt-4o", temperature=0)
    structured_model = model.with_structured_output(ContactInfo)

    result = structured_model.invoke(
        "从以下文本提取联系人: 王芳, wangfang@corp.cn, 13800138000"
    )
    print(f"类型: {type(result).__name__}")
    print(f"结果: {result}")
    print(f"邮箱: {result.email}")


def demo_structured_chain():
    """Prompt | structured_model — 结构化抽取链"""
    print("\n=== 结构化抽取 Chain ===")

    model = init_chat_model("openai:gpt-4o-mini", temperature=0)
    structured_model = model.with_structured_output(MovieInfo)

    prompt = ChatPromptTemplate.from_template(
        "从描述中提取电影信息，返回 title/year/genre:\n\n{text}"
    )
    chain = prompt | structured_model

    result = chain.invoke({
        "text": "《肖申克的救赎》是1994年上映的剧情片，讲述监狱中的希望与自由。"
    })
    print(f"片名: {result['title']}, 年份: {result['year']}, 类型: {result['genre']}")


# ========== 2. Agent 级结构化输出 ==========

def demo_agent_response_format():
    """create_agent(response_format=Schema) → structured_response"""
    print("\n=== Agent response_format (自动策略) ===")

    agent = create_agent(
        model="openai:gpt-4o",
        tools=[],
        response_format=ContactInfo,
    )

    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": "提取: 李明, liming@example.com, 010-88886666",
        }],
    })

    structured = result.get("structured_response")
    print(f"structured_response: {structured}")
    if structured:
        print(f"  姓名: {structured.name}, 电话: {structured.phone}")


def demo_agent_tool_strategy():
    """ToolStrategy — 显式指定工具调用实现结构化（兼容性更好）"""
    print("\n=== Agent ToolStrategy ===")

    from langchain.agents.structured_output import ToolStrategy

    agent = create_agent(
        model="openai:gpt-4o",
        tools=[],
        response_format=ToolStrategy(ProductReview),
    )

    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": (
                "分析评价: '手机拍照很棒，5星。就是电池不太耐用，价格偏贵。'"
            ),
        }],
    })

    review = result.get("structured_response")
    print(f"评价分析: {review}")
    if review:
        print(f"  情感: {review.sentiment}, 评分: {review.rating}")
        print(f"  要点: {review.key_points}")


# ========== 3. JSON Schema 形式 ==========

def demo_json_schema():
    """字典 JSON Schema — 不依赖 Pydantic 类"""
    print("\n=== JSON Schema 结构化 ===")

    review_schema = {
        "type": "object",
        "description": "产品评价分析",
        "properties": {
            "sentiment": {
                "type": "string",
                "enum": ["positive", "negative"],
            },
            "key_points": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["sentiment", "key_points"],
    }

    model = init_chat_model("openai:gpt-4o", temperature=0)
    structured_model = model.with_structured_output(review_schema)

    result = structured_model.invoke(
        "评价: '物流超快，包装破损，客服态度差。'"
    )
    print(f"结果 (dict): {result}")


# ========== 4. 结构化 + 自然语言回复并存 ==========

def demo_agent_with_tools_and_structure():
    """有工具时也可要求 structured_response（抽取类任务）"""
    print("\n=== 结构化输出 + 工具 Agent ===")

    from langchain.tools import tool

    @tool
    def word_count(text: str) -> int:
        """统计文本字数"""
        return len(text.replace(" ", ""))

    agent = create_agent(
        model="openai:gpt-4o",
        tools=[word_count],
        system_prompt="分析用户评价；需要统计字数时调用 word_count。",
        response_format=ProductReview,
    )

    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": "分析: 'Excellent quality and fast delivery! Five stars.'",
        }],
    })

    print(f"structured_response: {result.get('structured_response')}")
    last = result.get("messages", [])[-1] if result.get("messages") else None
    if last and hasattr(last, "content"):
        print(f"最后一条消息: {str(last.content)[:120]}...")


if __name__ == "__main__":
    print("=" * 60)
    print("12 - Structured Output: 结构化输出")
    print("=" * 60)

    demo_model_structured_output()
    demo_structured_chain()
    demo_agent_response_format()
    demo_agent_tool_strategy()
    demo_json_schema()
    demo_agent_with_tools_and_structure()

    print("\n核心要点:")
    print("1. Chain 用 model.with_structured_output(Schema)")
    print("2. Agent 用 response_format=Schema，结果在 structured_response")
    print("3. OpenAI 等支持原生结构化时用 ProviderStrategy（自动选择）")
    print("4. 其他模型用 ToolStrategy 通过工具调用返回 JSON")
    print("5. 结构化适合 API/数据库写入；聊天 UI 仍用自然语言流 (11_stream_memory)")
