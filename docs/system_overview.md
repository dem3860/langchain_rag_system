# 社内統合基盤システム (Internal Integrated Platform) - システム概要書

## 1. はじめに

本ドキュメントは、社内統合基盤システム（コードネーム: **Nexus**）のアーキテクチャおよび技術スタックについて記述します。
本システムは、全社的な従業員データ管理、認証認可、および各業務アプリケーションへのデータ供給を担う基幹システムです。

## 2. システムアーキテクチャ

本システムは、スケーラビリティと保守性を重視した **マイクロサービスアーキテクチャ** を採用しています。

### 2.1. 全体構成図 (概念)

```mermaid
graph TD
    Client[Web/Mobile Client] --> ALB[Application Load Balancer]
    ALB --> Gateway[API Gateway (Kong)]

    subgraph Services
        Gateway --> Auth[Auth Service (Keycloak)]
        Gateway --> User[User Service]
        Gateway --> HR[HR Service]
        Gateway --> Audit[Audit Log Service]
    end

    User --> DB_User[(PostgreSQL: Users)]
    HR --> DB_HR[(PostgreSQL: HR)]
    Audit --> DB_Audit[(TimescaleDB)]

    Services --> EventBus[Event Bus (Kafka)]
    EventBus --> Search[Search Service (Elasticsearch)]
```

### 2.2. 主要コンポーネント

| サービス名        | 役割                                                 | 技術スタック                 |
| ----------------- | ---------------------------------------------------- | ---------------------------- |
| **API Gateway**   | リクエストのルーティング、レート制限、認証オフロード | Kong, Nginx                  |
| **Auth Service**  | ID 管理、SSO (OIDC/SAML)、多要素認証                 | Keycloak, Redis              |
| **User Service**  | 従業員プロファイル管理、組織階層管理                 | Go, gRPC, PostgreSQL         |
| **HR Service**    | 人事評価、給与連携、勤怠データ集約                   | Python (FastAPI), PostgreSQL |
| **Audit Service** | 全操作ログの記録、監査レポート生成                   | Rust, TimescaleDB            |

## 3. インフラストラクチャ

- **Cloud Provider**: AWS (Amazon Web Services)
- **Container Orchestration**: Amazon EKS (Kubernetes 1.28)
- **IaC**: Terraform (State 管理は S3 + DynamoDB)
- **CI/CD**: GitHub Actions + ArgoCD

## 4. 監視・オブザーバビリティ

- **Metrics**: Prometheus + Grafana
- **Tracing**: OpenTelemetry + Jaeger
- **Logs**: Fluent Bit -> Amazon OpenSearch Service

## 5. 外部システム連携

- **Slack**: 通知および ChatOps 連携
- **Salesforce**: 営業データ連携 (Sync Job は夜間バッチ実行)
- **SmartHR**: 人事マスタ連携
