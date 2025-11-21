# Nexus API 設計ガイドライン (Ver 2.1)

## 1. 基本原則

- **RESTful**: リソース指向アーキテクチャを採用する。
- **JSON First**: リクエスト/レスポンスボディは原則として JSON (Content-Type: application/json) とする。
- **Stateless**: サーバー側でクライアントの状態（セッション等）を保持しない。

## 2. URL 設計

### 2.1. パス構成

`/api/{version}/{resource}/{id}/{sub-resource}` の形式とする。

- `version`: `v1`, `v2` など。破壊的変更がある場合のみメジャーバージョンを上げる。
- `resource`: 複数形の名詞 (ケバブケース)。
- `id`: UUID v4 を推奨。

**例:**

- `GET /api/v1/users` (ユーザー一覧取得)
- `GET /api/v1/users/123e4567-e89b-12d3-a456-426614174000/roles` (特定ユーザーのロール一覧)

### 2.2. クエリパラメータ

フィルタリング、ソート、ページネーションに使用する。スネークケースを使用。

- `?status=active` (フィルタ)
- `?sort=-created_at` (ソート: `-` は降順)
- `?page=2&per_page=50` (ページネーション)

## 3. レスポンスフォーマット

### 3.1. 成功時 (200 OK)

データは `data` フィールドに格納する。メタデータ（ページネーション等）は `meta` に格納する。

```json
{
  "data": [
    {
      "id": "123",
      "name": "Taro Yamada",
      "email": "taro@example.com"
    }
  ],
  "meta": {
    "total_count": 100,
    "page": 1,
    "per_page": 20
  }
}
```

### 3.2. エラー時 (4xx, 5xx)

RFC 7807 (Problem Details for HTTP APIs) に準拠することを推奨するが、最低限以下の形式を守ること。

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested user was not found.",
    "details": {
      "resource_id": "123"
    },
    "request_id": "req-abc-123"
  }
}
```

## 4. 認証・認可

- **Authentication**: `Authorization: Bearer <JWT>` ヘッダーを使用。
- **Scopes**: OAuth2 スコープによりエンドポイントへのアクセス制御を行う (例: `read:users`, `write:users`)。

## 5. レート制限 (Rate Limiting)

API Gateway 層で適用される。

- 制限超過時は `429 Too Many Requests` を返す。
- レスポンスヘッダに以下を含める:
  - `X-RateLimit-Limit`: 制限回数
  - `X-RateLimit-Remaining`: 残り回数
  - `X-RateLimit-Reset`: リセット時刻 (Unix Timestamp)
