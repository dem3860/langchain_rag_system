import os
from typing import Annotated, TypedDict, List

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# ========= 設定読み込み =========

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

DB_CONNECTION = os.getenv("DATABASE_URL")
COLLECTION_NAME = "internal_docs"
LLM_PROVIDER = os.getenv("LLM_PROVIDER")


# ========= LLM / Embeddings =========

def get_llm():
    if LLM_PROVIDER == "openai":
        return ChatOpenAI(model="gpt-4o", temperature=0)
    elif LLM_PROVIDER == "gemini":
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            api_key=api_key,
        )
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")


def get_embeddings():
    if LLM_PROVIDER == "openai":
        return OpenAIEmbeddings(model="text-embedding-3-small")
    elif LLM_PROVIDER == "gemini":
        return GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=api_key,
        )
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")


# ========= State 定義 =========

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    question: str
    context: str
    evaluation: str
    decision: str


# ========= Node 実装 =========

def receive_question(state: AgentState):
    """メッセージ履歴の末尾から質問文を取り出す"""
    messages = state["messages"]
    question = messages[-1].content if messages else ""
    return {"question": question}


def should_search(state: AgentState):
    """検索が必要かどうかを LLM に判定させる"""
    question = state["question"]
    llm = get_llm()

    prompt = ChatPromptTemplate.from_template(
        """
        あなたは社内ドキュメント検索システムのルーターです。
        以下のユーザの質問に対して、社内ドキュメントを検索する必要があるかどうかを判断してください。
        
        質問: {question}
        
        - 検索が必要な場合は "SEARCH"
        - 挨拶や一般的な会話など、検索が不要な場合は "NO_SEARCH"
        とだけ出力してください。
        """
    )

    chain = prompt | llm | StrOutputParser()
    decision = chain.invoke({"question": question}).strip()
    return {"decision": decision}


def retrieve(state: AgentState):
    """pgvector から類似ドキュメントを取得して context にまとめる"""
    question = state["question"]
    embeddings = get_embeddings()

    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=DB_CONNECTION,
        use_jsonb=True,
    )

    docs = vector_store.similarity_search(question, k=3)
    context = "\n\n".join([d.page_content for d in docs])
    return {"context": context}


def generate_answer(state: AgentState):
    """質問と（あれば）コンテキストから最終回答を生成する"""
    question = state["question"]
    context = state.get("context", "")
    llm = get_llm()

    if not context:
        # コンテキスト無しパターン
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "あなたは親切なアシスタントです。ユーザの質問に、分かりやすく簡潔に答えてください。"
            ),
            ("human", "{question}"),
        ])
        chain = prompt | llm | StrOutputParser()
        answer = chain.invoke({"question": question})

    else:
        # コンテキスト有り RAG パターン
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                あなたは社内ドキュメント検索アシスタントです。
                以下のコンテキストを可能な限り参照しながら、ユーザの質問に答えてください。
                コンテキストに関連情報がない場合は、
                「提供されている社内ドキュメントの範囲では情報が見つかりませんでした。」と答えてください。
                
                コンテキスト:
                {context}
                """
            ),
            ("human", "{question}"),
        ])
        chain = prompt | llm | StrOutputParser()
        answer = chain.invoke({
            "question": question,
            "context": context,
        })

    return {"messages": [AIMessage(content=answer)]}


def evaluate_answer(state: AgentState):
    """生成した回答が質問・コンテキストに対して妥当か簡易評価する"""
    last_answer = state["messages"][-1].content
    question = state["question"]
    context = state.get("context", "")
    llm = get_llm()

    prompt = ChatPromptTemplate.from_template(
        """
        あなたは回答の品質評価者です。
        以下の回答が、質問およびコンテキストに基づいて適切かどうかを判定してください。
        
        質問: {question}
        コンテキスト: {context}
        回答: {last_answer}
        
        - 質問にきちんと答えており、コンテキストも適切に活用されている場合は "GOOD"
        - 質問に答えていない / コンテキストを無視している / 明らかに不十分な場合は "BAD"
        とだけ出力してください。
        """
    )

    chain = prompt | llm | StrOutputParser()
    evaluation = chain.invoke({
        "question": question,
        "context": context,
        "last_answer": last_answer,
    }).strip()

    return {"evaluation": evaluation}


def final_output(state: AgentState):
    """最終ノード（ここでは特に状態をいじらずそのまま終了）"""
    return {}


# ========= グラフ構築 =========

def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("receive_question", receive_question)
    workflow.add_node("should_search", should_search)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("generate_answer", generate_answer)
    workflow.add_node("evaluate_answer", evaluate_answer)
    workflow.add_node("final_output", final_output)

    workflow.set_entry_point("receive_question")

    # receive_question → should_search
    workflow.add_edge("receive_question", "should_search")

    # should_search の判定結果でルーティング
    def route_search(state: AgentState):
        return "retrieve" if state.get("decision") == "SEARCH" else "generate_answer"

    workflow.add_conditional_edges(
        "should_search",
        route_search,
        {
            "retrieve": "retrieve",
            "generate_answer": "generate_answer",
        },
    )

    # retrieve → generate_answer
    workflow.add_edge("retrieve", "generate_answer")

    # generate_answer → evaluate_answer
    workflow.add_edge("generate_answer", "evaluate_answer")

    # 評価結果は今回はログ用途なので、常に final_output へ
    def route_eval(state: AgentState):
        return "final_output"

    workflow.add_conditional_edges(
        "evaluate_answer",
        route_eval,
        {
            "final_output": "final_output",
        },
    )

    # final_output → END
    workflow.add_edge("final_output", END)

    return workflow.compile()


app = build_graph()
