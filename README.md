# FastAPI Template

FastAPI プロジェクトを素早く立ち上げるためのテンプレートリポジトリです。
DynamoDB と PostgreSQL の両方をサポートし、厳格なコーディングガイドラインに基づいた保守性の高い設計を提供します。

## 特徴

- **複数のデータベースサポート**: DynamoDB と PostgreSQL の実装例を同梱
- **サンプル実装**: モック API ジェネレーターをサンプルとして実装済み
- **厳格なコーディング規約**: Ruff と mypy による厳格な型チェックとコード品質管理
- **高速な開発環境**: パッケージマネージャー `uv` と Docker Compose を使用した高速なセットアップ
- **テンプレートリポジトリ**: GitHub のテンプレート機能により、新規プロジェクトを即座に開始可能
- **自動初期化**: テンプレートから作成時に、プロジェクト名を自動的に設定

## 技術スタック

- **言語**: Python 3.12+
- **フレームワーク**: FastAPI
- **データベース**: Amazon DynamoDB / PostgreSQL
- **パッケージ管理**: uv
- **開発環境**: Docker Compose
- **コード品質**: Ruff, mypy, pytest

## テンプレートの使い方

### 1. テンプレートからリポジトリを作成

GitHub 上でこのリポジトリの「Use this template」ボタンをクリックし、新しいリポジトリを作成します。

### 2. 自動初期化

初回のプッシュ時に、GitHub Actions が自動的に以下を実行します：

- `app/pyproject.toml` のプロジェクト名をリポジトリ名に更新
- `docker-compose.yaml` のサービス名とボリューム名をリポジトリ名に更新

### 3. ローカル開発環境のセットアップ

#### 前提条件

- Docker Desktop (または Docker Engine + Docker Compose)

#### 起動方法

1. **環境変数の設定**

   `.env` ファイルを作成します（PostgreSQL 用）：

   ```bash
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=mydb
   ```

2. **コンテナのビルドと起動**
   サンプル実装について

このテンプレートには、モック API ジェネレーターがサンプル実装として含まれています。
実際のプロジェクトでは、このサンプルコードを参考にしながら、独自のドメインロジックに置き換えてください。

### サンプル API の利用例

#### 1. ヘルスチェック

```bash
curl http://localhost:8080/
```

#### 2. モックエンドポイントの作成

```bash
curl -X POST http://localhost:8080/api/mocks \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/test-endpoint",
    "method": "GET",
    "status_code": 200,
    "response_body": {"message": "This is a mock response"},
    "headers": {"X-Custom-Header": "mock-value"},
    "latency_ms": 500
  }'
```

#### 3. モックエンドポイントの呼び出し

```bash
curl -v http://localhost:8080/test-endpoint
```

#### 4. モックエンドポイントの削除

```bash
curl -X DELETE http://localhost:8080/api/mocks/{mock_id}
```

## コーディングガイドライン

このテンプレートは、以下の厳格なガイドラインに従っています：

- **型安全性**: mypy の strict モードによる完全な型チェック
- **コード品質**: Ruff による厳格なリント（複雑度制限、命名規則、Any 型禁止など）
- **最小限の OOP**: 必要最小限のクラス使用、関数型アプローチの優先
- **明確な責務分離**: ドメイン、インフラストラクチャ、共有レイヤーの明確な分離

詳細は `app/docs/` 配下のドキュメントを参照してください

````

### 3. モックエンドポイントの呼び出し

```bash
curl -v http://localhost:8080/test-endpoint
````

### 4. モックエンドポイントの削除

作成時に返却された ID を指定して削除します。

```bash
curl -X DELETE http://localhost:8080/api/mocks/{mock_id}
```

## 本番デプロイ (AWS Lambda)

本プロジェクトは AWS Lambda Web Adapter を使用しています。

1. **本番用イメージのビルド**

   ```bash
   docker build -f Dockerfile.prod -t my-mock-api .
   ```

2. **デプロイ手順の概要**
   - ビルドしたイメージを Amazon ECR にプッシュします。
   - AWS Lambda 関数を作成し、コンテナイメージとしてプッシュしたイメージを指定します。
   - 環境変数を設定します（`DYNAMODB_ENDPOINT_URL` は本番では不要、AWS 認証情報は IAM ロールで管理）。
   - 必要に応じて DynamoDB テーブル (`MockEndpoints`) を作成します。

## ディレクトリ構成

```
.
├── .github/
│   └── workflows/
│       └── init.yaml                  # テンプレート初期化ワークフロー
├── app/
│   ├── docs/                          # 設計ドキュメント・ガイドライン
│   ├── scripts/                       # DB 初期化スクリプト
│   ├── src/
│   │   ├── domain/                    # ドメインロジック（サンプル: モック API）
│   │   ├── infrastructure/            # インフラストラクチャ層（DynamoDB, PostgreSQL）
│   │   └── shared/                    # 共有ユーティリティ
│   ├── tests/                         # テストコード
│   └── pyproject.toml                 # 依存関係定義
├── Dockerfile.dev                     # 開発用 Dockerfile
├── Dockerfile.prod                    # 本番用 Dockerfile
├── docker-compose.yaml                # ローカル開発環境定義
└── test_*.sh                          # 動作確認スクリプト
```

## カスタマイズ

1. **サンプル実装の削除**: `app/src/domain/mocks/` を削除し、独自のドメインロジックを実装
2. **データベースの選択**: DynamoDB または PostgreSQL、あるいは両方を使用
3. **設定のカスタマイズ**: `app/src/config.py` で環境変数や設定を追加
4. **ルーターの追加**: `app/src/main.py` でルーターを登録

## ライセンス

このテンプレートは自由に使用・改変できます。
