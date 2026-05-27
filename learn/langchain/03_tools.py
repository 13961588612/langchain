"""
03_tools.py - 工具定义与使用

学习要点:
1. @tool 装饰器: 最简单的工具定义方式
2. StructuredTool: 带复杂参数 Schema 的工具
3. 工具组合: 让 LLM 自主选择调用哪个工具
4. ToolException: 工具错误处理
"""
import os
import json
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from langchain.tools import tool, StructuredTool
from langchain.messages import HumanMessage, SystemMessage
from model import getModel


# ========== 1. @tool 装饰器: 最简单的工具 ==========

@tool
def get_current_time() -> str:
    """获取当前的日期和时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def calculate(expression: str) -> str:
    """执行数学计算。expression 是数学表达式，例如 '2 + 3 * 4'"""
    try:
        # 安全评估（仅允许数学运算）
        allowed_names = {"__builtins__": {}}
        result = eval(expression, allowed_names, {})
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


@tool
def search_knowledge(query: str) -> str:
    """搜索内部知识库（模拟）。query 是搜索关键词"""
    # 模拟知识库
    knowledge_base = {
        "langchain": "LangChain 是一个用于构建 LLM 应用的框架，支持 Chains、Agents、Tools 等核心概念。",
        "langgraph": "LangGraph 是 LangChain 的状态图编排框架，使用 StateGraph 构建多步骤 Agent 工作流。",
        "agent": "AI Agent（智能体）是能够自主感知环境、做出决策、使用工具来完成任务的 AI 系统。",
        "rag": "RAG（检索增强生成）是一种结合检索和生成的技术，先从知识库检索相关文档，再让 LLM 基于检索结果生成答案。",
        "tool": "Tool（工具）是 Agent 可以用来执行特定操作的功能组件，如搜索、计算、API 调用等。",
        "chain": "Chain（链）是 LangChain 中将多个组件串联起来执行的工作流，如 LLMChain、SequentialChain。",
    }

    query_lower = query.lower()
    results = []
    for key, value in knowledge_base.items():
        if key in query_lower or any(word in value for word in query_lower.split()):
            results.append(f"[{key}]: {value}")

    if results:
        return "\n\n".join(results)
    return f"未找到与 '{query}' 相关的知识。"


# ========== 2. StructuredTool: 复杂参数 ==========

def get_weather(city: str, unit: Optional[str] = "celsius") -> str:
    """获取指定城市的天气信息（模拟）

    Args:
        city: 城市名称
        unit: 温度单位，celsius 或 fahrenheit
    """
    # 模拟天气数据
    weather_data = {
        "北京": {"temp": 22, "condition": "晴"},
        "上海": {"temp": 28, "condition": "多云"},
        "深圳": {"temp": 31, "condition": "阵雨"},
        "东京": {"temp": 25, "condition": "晴"},
        "纽约": {"temp": 15, "condition": "阴"},
    }
    data = weather_data.get(city, {"temp": 20, "condition": "未知"})
    temp = data["temp"]
    if unit == "fahrenheit":
        temp = temp * 9 / 5 + 32

    return json.dumps({
        "city": city,
        "temperature": round(temp, 1),
        "unit": unit,
        "condition": data["condition"],
    }, ensure_ascii=False)


weather_tool = StructuredTool.from_function(
    func=get_weather,
    name="get_weather",
    description="获取指定城市的天气信息",
)


# ========== 3. 工具组合: Agent 自主选择 ==========

def demo_tool_binding():
    """演示将工具绑定到 LLM，让模型自主决定调用哪个工具"""
    print("\n=== 工具绑定 (Tool Binding) ===")

    model = getModel(temperature=0)
    tools = [get_current_time, calculate, search_knowledge, weather_tool]

    # 绑定工具到模型
    model_with_tools = model.bind_tools(tools)

    test_queries = [
        "现在几点？",
        "帮我算一下 123 * 456 + 789",
        "什么是 RAG？",
        "北京今天天气怎么样？",
    ]

    for query in test_queries:
        print(f"\n用户: {query}")
        response = model_with_tools.invoke([HumanMessage(content=query)])

        # 检查模型是否想调用工具
        if response.tool_calls:
            for tool_call in response.tool_calls:
                print(f"  -> 调用工具: {tool_call['name']}")
                print(f"     参数: {tool_call['args']}")

                # 执行工具
                tool_map = {t.name: t for t in tools}
                selected_tool = tool_map.get(tool_call["name"])
                if selected_tool:
                    result = selected_tool.invoke(tool_call["args"])
                    print(f"     结果: {result}")
        else:
            print(f"  直接回复: {response.content}")


def demo_manual_tool_call():
    """演示手动调用工具（适合教学理解底层机制）"""
    print("\n=== 手动工具调用 ===")

    # 直接调用工具
    print("get_current_time():", get_current_time.invoke({}))
    print("calculate('2 ** 10'):", calculate.invoke({"expression": "2 ** 10"}))
    print("search_knowledge('agent'):", search_knowledge.invoke({"query": "agent"}))

    # 使用 StructuredTool
    print("\nget_weather('深圳'):", weather_tool.invoke({"city": "深圳"}))
    print("get_weather('纽约', 'fahrenheit'):",
          weather_tool.invoke({"city": "纽约", "unit": "fahrenheit"}))

    # 查看工具的 Schema
    print("\n工具 Schema 示例:")
    print(f"calculate 参数: {calculate.args_schema.schema()}")
    print(f"weather_tool 参数: {weather_tool.args_schema.schema()}")


if __name__ == "__main__":
    print("=" * 60)
    print("03 - Tools: 工具定义与使用")
    print("=" * 60)

    demo_manual_tool_call()
    demo_tool_binding()

    # print("\n核心要点:")
    # print("1. @tool 装饰器快速定义工具，docstring 会被用作工具描述")
    # print("2. StructuredTool 支持带复杂参数 Schema 的工具")
    # print("3. model.bind_tools() 让 LLM 自主决定调用哪些工具")
    # print("4. 工具描述的质量直接影响 LLM 选择工具的正确性")
