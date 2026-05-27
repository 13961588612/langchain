"""
06_rag.py - RAG (检索增强生成) 全流程

学习要点:
1. Document Loader: 加载多种格式文档
2. Text Splitter: 智能文本分块
3. Embeddings: 文本向量化
4. VectorStore: 向量相似度检索
5. Retriever: 检索器抽象
6. QA Chain: 基于检索结果的问答

全流程: Loader → Splitter → Embeddings → VectorStore → Retriever → QA
"""
import os
from dotenv import load_dotenv

load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document

# 文档加载与分割
from langchain_community.document_loaders import TextLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Embedding 与向量存储
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma


def demo_document_loading():
    """演示文档加载"""
    print("\n=== 文档加载 ===")

    # 方式1: 从文本加载
    sample_text = """
    LangChain 是一个用于开发由语言模型驱动的应用程序的框架。
    它提供了以下核心模块:
    1. Model I/O: 与语言模型交互
    2. Retrieval: 与应用程序特定数据交互
    3. Agents: 让 LLM 决定使用哪些工具
    4. Chains: 构建调用序列
    5. Memory: 在链调用之间持久化状态
    6. Callbacks: 记录和流式传输中间步骤

    LangGraph 是 LangChain 的状态图编排框架。
    它使用有向图来定义 Agent 工作流:
    - StateGraph: 定义状态和节点
    - Node: 图中的执行单元
    - Edge: 节点之间的连接
    - Conditional Edge: 条件路由
    - Checkpointing: 状态持久化和恢复
    - Human-in-the-Loop: 人工审批节点

    RAG (检索增强生成) 是让 LLM 基于外部知识库回答问题的技术。
    RAG 的工作流程:
    1. 将文档分割成小块 (chunks)
    2. 将每个块转换为向量 (embeddings)
    3. 存入向量数据库 (vector store)
    4. 用户提问时检索最相关的块
    5. 将检索结果作为上下文传给 LLM
    6. LLM 基于上下文生成答案
    """

    # 写入临时文件
    tmp_path = "temp_knowledge.txt"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(sample_text)

    loader = TextLoader(tmp_path, encoding="utf-8")
    documents = loader.load()

    print(f"加载了 {len(documents)} 个文档")
    print(f"第一篇文档前150字: {documents[0].page_content[:150]}...")

    # 清理临时文件
    os.remove(tmp_path)
    return documents


def demo_text_splitting(documents: list[Document]):
    """演示文本分割"""
    print("\n=== 文本分割 ===")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,         # 每块最大字符数
        chunk_overlap=40,       # 块之间重叠字符数（保持上下文连贯）
        separators=["\n\n", "\n", "。", ".", " ", ""],  # 优先按段落/句子分割
    )

    chunks = text_splitter.split_documents(documents)

    print(f"分割成了 {len(chunks)} 个块")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1} (长度 {len(chunk.page_content)}): {chunk.page_content[:80]}...")
    return chunks


def demo_embeddings_and_vectorstore(chunks: list[Document]):
    """演示向量化和存储"""
    print("\n=== Embedding + VectorStore ===")

    # 使用 OpenAI Embedding 模型
    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    except Exception as e:
        print(f"OpenAI Embedding 不可用: {e}")
        print("(跳过向量存储演示，但代码逻辑完整)")
        return None

    # 创建 Chroma 向量存储（内存模式）
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name="langchain_knowledge",
    )

    print(f"向量存储包含 {vectorstore._collection.count()} 个向量")

    # 演示相似度检索
    query = "什么是 RAG？"
    results = vectorstore.similarity_search(query, k=2)

    print(f"\n查询: '{query}'")
    print("最相关的文档块:")
    for i, doc in enumerate(results):
        print(f"  Top {i+1}: {doc.page_content[:100]}...")

    return vectorstore


def demo_rag_qa_chain(vectorstore):
    """演示完整的 RAG 问答链"""
    print("\n=== RAG 问答链 ===")

    if vectorstore is None:
        print("(跳过: 需要 Embedding API)")
        return

    model = init_chat_model("openai:gpt-4o", temperature=0.3)

    # 从 vectorstore 创建 retriever
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3},
    )

    # RAG Prompt 模板
    rag_prompt = ChatPromptTemplate.from_template("""
你是一个基于知识库的问答助手。请使用以下检索到的上下文来回答问题。
如果上下文中没有相关信息，请如实说不知道。

上下文:
{context}

问题: {question}

回答:""")

    def format_docs(docs):
        """将检索到的文档格式化为上下文字符串"""
        return "\n\n".join([f"[来源 {i+1}]: {doc.page_content}" for i, doc in enumerate(docs)])

    # 构建 RAG Chain
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | rag_prompt
        | model
        | StrOutputParser()
    )

    # 测试问答
    questions = [
        "什么是 RAG？它的工作流程是怎样的？",
        "LangChain 有哪些核心模块？",
        "LangGraph 是什么？",
        "今天天气怎么样？",  # 不在知识库中
    ]

    for q in questions:
        print(f"\nQ: {q}")
        answer = rag_chain.invoke(q)
        print(f"A: {answer}")


if __name__ == "__main__":
    print("=" * 60)
    print("06 - RAG: 检索增强生成全流程")
    print("=" * 60)

    # 全流程演示
    documents = demo_document_loading()
    chunks = demo_text_splitting(documents)
    vectorstore = demo_embeddings_and_vectorstore(chunks)
    demo_rag_qa_chain(vectorstore)

    print("\n核心要点:")
    print("1. Document Loader 支持 TXT/PDF/Web/Markdown 等多种格式")
    print("2. RecursiveCharacterTextSplitter 优先按语义边界分割（段落>句子>字符）")
    print("3. chunk_overlap 保证块之间的上下文连贯性")
    print("4. Embedding 将文本转为向量，语义相近的文本向量距离更近")
    print("5. VectorStore.similarity_search() 用余弦相似度检索最相关块")
    print("6. RAG Chain: retriever | format_docs | prompt | model | parser")
