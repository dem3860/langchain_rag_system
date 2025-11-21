# Nexus システム トラブルシューティング・運用ガイド

## 1. インシデント対応フロー

障害発生時は、以下のフローに従って対応してください。

1. **検知**: Datadog アラート または ユーザー報告
2. **一次切り分け**: ステータスページ確認、ログ確認
3. **エスカレーション**: 重大度 (Severity 1-3) に応じて `#incident-response` チャンネルで報告
4. **対応**: 暫定対応（ロールバック、再起動など）
5. **恒久対策**: ポストモーテム作成、修正パッチ適用

## 2. よくあるエラーと対処法

### 2.1. Database Connection Error (PostgreSQL)

**症状**: アプリケーションログに `FATAL: remaining connection slots are reserved for non-replication superuser connections` が出る。
**原因**: コネクションプール (PgBouncer) の枯渇。
**対処**:

1. 現在の接続数を確認: `SELECT count(*) FROM pg_stat_activity;`
2. アイドル接続が多い場合、アプリケーション側の接続リークを疑う。
3. 緊急時は PgBouncer を再起動: `kubectl rollout restart deployment/pgbouncer`

### 2.2. Kubernetes Pod CrashLoopBackOff

**症状**: `kubectl get pods` でステータスが `CrashLoopBackOff` になる。
**原因**:

- アプリケーションの起動時エラー（環境変数不足、DB 接続失敗）
- OOMKilled (メモリ不足)
  **対処**:

1. ログ確認: `kubectl logs <pod-name> --previous`
2. OOM の場合: `kubectl describe pod <pod-name>` で `Last State: OOMKilled` を確認し、`resources.limits.memory` を緩和する。

### 2.3. API Gateway 504 Gateway Timeout

**症状**: クライアントに 504 エラーが返る。
**原因**: バックエンドサービスの応答遅延 (デフォルト 60 秒)。
**対処**:

1. Jaeger でトレースを確認し、ボトルネック（遅い SQL クエリ、外部 API 呼び出し）を特定する。
2. 一時的な高負荷の場合、HPA (Horizontal Pod Autoscaler) の設定を確認し、最大レプリカ数を増やす。

## 3. 運用コマンド集

### 3.1. ログ検索 (CloudWatch Logs Insights)

特定のリクエスト ID でエラーログを検索するクエリ例:

```sql
fields @timestamp, @message
| filter request_id = "req-abc-123"
| filter level = "ERROR"
| sort @timestamp desc
```

### 3.2. DB マイグレーション (Alembic)

手動でマイグレーションを適用する場合（踏み台サーバーより実行）:

```bash
export DATABASE_URL="postgresql://..."
alembic upgrade head
```
