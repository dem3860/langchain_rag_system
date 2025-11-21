# LangChain x LangGraph RAG System

社内ドキュメント検索を模した RAG (Retrieval-Augmented Generation) エージェントシステムです。
LangChain と LangGraph を使用し、質問のルーティング、検索、回答生成、そして回答の自己評価を行うエージェントを実装しています。
Vector Store には PostgreSQL (pgvector) を使用しています。

## プロジェクトの概要

このシステムは、以下のフローでユーザの質問に回答します。

1. **Router**: ユーザの質問がドキュメント検索を必要とするか判断します（挨拶などは検索しません）。
2. **Retrieve**: 検索が必要な場合、pgvector から関連ドキュメントを取得します。
3. **Generate**: LLM がコンテキストに基づいて回答を生成します。
4. **Evaluate**: 生成された回答が適切か（幻覚がないか、質問に答えているか）を自己評価します。

## ディレクトリ構成

```
.
├── agent.py            # LangGraph によるエージェントのコアロジック (ノード・グラフ定義)
├── ingest.py           # ドキュメントの埋め込み・保存を行うスクリプト
├── run.py              # エージェントを対話形式で実行する CLI ランナー
├── docker-compose.yml  # PostgreSQL (pgvector) の構成定義
├── pyproject.toml      # 依存ライブラリ定義
├── .env.example        # 環境変数のサンプル
└── docs/               # RAG の検索対象となる擬似社内ドキュメント群
    ├── system_overview.md
    ├── api_guidelines.md
    ├── troubleshooting.md
    ├── security_policy.md
    └── onboarding_manual.md
```

## インストール方法

前提: Python 3.12+, Docker Desktop, `uv` がインストールされていること。

1. **リポジトリのクローン**

   ```bash
   git clone <repository-url>
   cd langchain_rag_system
   ```

2. **依存関係のインストール**

   ```bash
   uv sync
   ```

3. **環境変数の設定**
   `.env.example` をコピーして `.env` を作成し、API キーを設定してください。

   ```bash
   cp .env.example .env
   ```

   - `LLM_PROVIDER`: `openai` または `gemini`
   - `OPENAI_API_KEY` / `GEMINI_API_KEY`: 各種 API キー

4. **データベースの起動**
   ```bash
   docker-compose up -d
   ```

## 実行方法

### 1. ドキュメントの埋め込み (Ingestion)

初回実行時や `docs/` 内のファイルを更新した際は、以下のコマンドでベクトルデータベースにデータを登録します。

```bash
uv run ingest.py
```

### 2. エージェントの起動

対話型インターフェースを起動して質問を行います。

```bash
uv run run.py
```

**実行例:**

```
User: APIの命名規則は？
Agent: APIの命名規則は以下の通りです...
```

## 技術スタック

- **Language**: Python 3.12
- **Orchestration**: LangChain, LangGraph
- **Vector Store**: PostgreSQL (pgvector)
- **LLM**: OpenAI (GPT-4o) / Google Gemini (Gemini 1.5 Pro)
- **Package Manager**: uv
