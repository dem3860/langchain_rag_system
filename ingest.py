import os
import glob
from typing import List

from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector
from langchain_core.documents import Document
from langchain_core.indexing import index
from langchain_classic.indexes import SQLRecordManager

# 環境変数の読み込み
load_dotenv()

# 設定関連
DB_CONNECTION = os.getenv("DATABASE_URL")
COLLECTION_NAME = "internal_docs"
LLM_PROVIDER = os.getenv("LLM_PROVIDER")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# embeddingモデルの設定と初期化(今回はgeminiの無料枠のみを使用するが、
# openaiの有料枠を使用することもできるように拡張した)
def get_embeddings():
    if LLM_PROVIDER == "openai":
        return OpenAIEmbeddings(model="text-embedding-3-small")
    elif LLM_PROVIDER == "gemini":
        return GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=GEMINI_API_KEY,
        )
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")


def load_documents() -> List[Document]:
    docs = []
    # docsディレクトリにあるすべてのmarkdownファイルを読み込む
    files = glob.glob("docs/*.md")
    print(f"Found {len(files)} documents in docs/")
    
    for file_path in files:
        print(f"Loading {file_path}...")
        loader = TextLoader(file_path)
        docs.extend(loader.load())
    
    return docs

# 文書の分割(今回は1000文字ごとに分割するが、200文字の重複を設けることで、文脈を保持することができる)
def split_documents(docs: List[Document]) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=1000,
        chunk_overlap=200,
    )
    return text_splitter.split_documents(docs)

def ingest():
    print("Starting ingestion process...")
    
    # 1. ドキュメントを読み込む
    raw_docs = load_documents()
    if not raw_docs:
        print("No documents found. Exiting.")
        return

    # 2. 文書を分割する
    splitted_docs = split_documents(raw_docs)
    print(f"Split into {len(splitted_docs)} chunks.")

    # 3. embeddingモデルを初期化する
    embeddings = get_embeddings()
    print(f"Using embeddings: {LLM_PROVIDER}")

    # 4. PGVectorを初期化する
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=DB_CONNECTION,
        use_jsonb=True,
    )

    # 5. レコードマネージャを初期化する
    namespace = f"pgvector/{COLLECTION_NAME}"
    record_manager = SQLRecordManager(
        namespace=namespace,
        db_url=DB_CONNECTION,
    )
    
    # レコードマネージャのスキーマを作成
    print("Creating record manager schema...")
    record_manager.create_schema()

    # 6. 文書をベクトルストアに追加する
    print("Indexing documents to pgvector with record manager...")
    result = index(
        splitted_docs,
        record_manager=record_manager,
        vector_store=vector_store,
        cleanup="incremental",
        source_id_key="source",
        key_encoder="sha256"
    )
    
    print(f"Ingestion complete! Added: {result['num_added']}, Updated: {result['num_updated']}, Deleted: {result['num_deleted']}, Skipped: {result['num_skipped']}")

if __name__ == "__main__":
    ingest()
