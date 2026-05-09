"""
02_prompt_templates.py - Prompt 模板系统

学习要点:
1. ChatPromptTemplate: 结构化多角色消息模板
2. MessagesPlaceholder: 动态插入历史对话
3. Few-shot prompting: 少样本提示
4. PipelinePrompt: 组合多个模板
"""
import os
from dotenv import load_dotenv

load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    FewShotChatMessagePromptTemplate,
    PipelinePromptTemplate,
)


def demo_basic_template():
    """最基础的模板: 变量替换"""
    print("\n=== 基础模板 ===")
    template = ChatPromptTemplate.from_messages([
        ("system", "你是一个{role}。请用{language}回答。"),
        ("human", "{question}"),
    ])

    # 填充变量
    prompt_value = template.invoke({
        "role": "Python 编程专家",
        "language": "中文",
        "question": "列表推导式和生成器表达式的区别是什么？",
    })

    # prompt_value 可以直接传给 model
    print("生成的 SystemMessage:", prompt_value.messages[0].content)
    print("生成的 HumanMessage:", prompt_value.messages[1].content)


def demo_with_history():
    """模板 + 对话历史: 使用 MessagesPlaceholder"""
    print("\n=== 带对话历史的模板 ===")
    template = ChatPromptTemplate.from_messages([
        ("system", "你是一个乐于助人的助手。"),
        MessagesPlaceholder(variable_name="history"),  # 动态插入历史消息
        ("human", "{question}"),
    ])

    # 模拟历史对话
    from langchain.messages import HumanMessage, AIMessage

    history = [
        HumanMessage(content="我叫小明"),
        AIMessage(content="你好小明！有什么可以帮助你的？"),
    ]

    prompt_value = template.invoke({
        "history": history,
        "question": "我叫什么名字？",
    })

    for i, msg in enumerate(prompt_value.messages):
        print(f"消息 {i} [{type(msg).__name__}]: {msg.content}")


def demo_few_shot():
    """少样本提示 (Few-shot): 给模型示例来引导输出格式"""
    print("\n=== Few-shot 少样本提示 ===")

    # 定义示例
    examples = [
        {
            "input": "今天天气真好",
            "output": "情感: 正面 | 强度: 中等 | 关键词: 天气"
        },
        {
            "input": "我讨厌这个 bug",
            "output": "情感: 负面 | 强度: 强烈 | 关键词: bug"
        },
        {
            "input": "吃完饭就回家了",
            "output": "情感: 中性 | 强度: 弱 | 关键词: 吃饭, 回家"
        },
    ]

    example_prompt = ChatPromptTemplate.from_messages([
        ("human", "{input}"),
        ("ai", "{output}"),
    ])

    few_shot_prompt = FewShotChatMessagePromptTemplate(
        example_prompt=example_prompt,
        examples=examples,
    )

    final_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个情感分析助手。分析输入的情感并输出格式。"),
        few_shot_prompt,
        ("human", "{input}"),
    ])

    # 测试
    prompt_value = final_prompt.invoke({"input": "这个电影还行吧，不算特别好但也过得去"})

    print("完整的 Few-shot Prompt:")
    for msg in prompt_value.messages:
        print(f"  [{type(msg).__name__}]: {msg.content}")

    # 实际调用模型
    model = init_chat_model("openai:gpt-4o", temperature=0.3)
    response = model.invoke(prompt_value)
    print(f"\n模型回复: {response.content}")


def demo_pipeline_prompt():
    """管道模板: 组合多个 Prompt 模板"""
    print("\n=== Pipeline Prompt 管道模板 ===")

    # 第一步: 角色定义
    persona_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个{persona}。"),
    ])

    # 第二步: 任务指令
    task_prompt = ChatPromptTemplate.from_messages([
        ("system", "你的任务是: {task}"),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
    ])

    # 第三步: 输出格式要求
    format_prompt = ChatPromptTemplate.from_messages([
        ("system", "请用 JSON 格式输出结果。"),
    ])

    # 组合为管道
    full_prompt = PipelinePromptTemplate(
        final_prompt=task_prompt,
        pipeline_prompts=[
            ("persona_block", persona_prompt),
            ("format_block", format_prompt),
        ],
    )

    # 注意: PipelinePromptTemplate 会自动将 pipeline_prompts 的变量
    # 合并到 final_prompt 中
    try:
        prompt_value = full_prompt.invoke({
            "persona": "代码审查专家",
            "task": "审查以下代码的安全性",
            "input": "def login(user): return eval(user.password)",
        })
        print("组合后的 System Messages:")
        for msg in prompt_value.messages:
            if hasattr(msg, "content"):
                print(f"  [{type(msg).__name__}]: {msg.content[:100]}")
    except Exception as e:
        print(f"PipelinePrompt 示例（不同版本的 API 略有差异）: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("02 - Prompt Templates: 模板系统")
    print("=" * 60)

    demo_basic_template()
    demo_with_history()
    demo_few_shot()
    demo_pipeline_prompt()

    print("\n核心要点:")
    print("1. ChatPromptTemplate.from_messages() 构建多角色消息模板")
    print("2. MessagesPlaceholder 动态插入历史对话")
    print("3. FewShotChatMessagePromptTemplate 提供示例引导输出")
    print("4. PipelinePromptTemplate 组合多个模板")
