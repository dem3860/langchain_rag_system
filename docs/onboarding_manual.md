# 開発者オンボーディングマニュアル (Developer Setup Guide)

## 1. はじめに

Nexus プロジェクトへようこそ！
このドキュメントは、開発環境を最短で構築し、最初の Pull Request を出すまでの手順をまとめたものです。

## 2. 前提条件 (Prerequisites)

以下のツールがインストールされていることを確認してください。

- **OS**: macOS (Ventura 以上) or Linux (Ubuntu 22.04 LTS)
- **Docker Desktop**: v4.20+ (Resource 設定: CPU 4core, Mem 8GB 以上推奨)
- **Python**: 3.12 (pyenv 推奨)
- **Node.js**: v20 (LTS)
- **AWS CLI v2**: SSO 設定済みであること

## 3. 環境構築手順

### 3.1. リポジトリのセットアップ

```bash
# SSH設定がまだの場合は先にGitHubに公開鍵を登録してください
git clone git@github.com:internal/nexus-monorepo.git
cd nexus-monorepo

# uv (高速パッケージマネージャ) のインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# 依存関係のインストール
uv sync --all-extras
```

### 3.2. プリコミットフックの導入

コード品質を保つため、pre-commit を導入しています。

```bash
uv run pre-commit install
```

これにより、コミット時に自動的に `ruff` (Linter) と `black` (Formatter) が走ります。

### 3.3. ローカル開発環境の起動

Docker Compose を使用して、DB (PostgreSQL), Redis, LocalStack (AWS Mock) を起動します。

```bash
# 環境変数の準備
cp .env.example .env
# 1Password から開発用シークレットを取得して .env を埋める
op read "op://Engineering/Nexus-Dev/env" > .env

# コンテナ起動
docker-compose up -d

# マイグレーション実行
uv run alembic upgrade head

# サーバー起動
uv run uvicorn app.main:app --reload --port 8000
```

## 4. 開発フロー

1. Jira チケットを確認し、feature ブランチを作成 (`feature/NEX-1234-add-login`)
2. 実装 & テストコード作成 (`pytest` でテスト実行)
3. PR 作成 (テンプレートに従って記述)
4. CI (GitHub Actions) のパスを確認
5. レビュー依頼 (Reviewers にチームを指定)

## 5. 困ったときは

- **ドキュメント**: `docs/` 以下のマークダウン、または Notion の「Nexus 開発ナレッジ」を参照。
- **Slack**: `#dev-nexus` チャンネルで質問してください。エラーログと再現手順を添えるとスムーズです。
