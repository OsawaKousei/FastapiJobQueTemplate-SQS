# Phase 3 to Phase 4 引継ぎドキュメント

## 1. 現状ステータス (Status)

Phase 3 (Infrastructure & Persistence) まで完了しています。
DynamoDB を使用した Repository パターンの実装と、ローカル DynamoDB コンテナを用いた統合テストがパスしています。

## 2. 実装済みコンポーネント (Implemented Components)

### 2.0 Configuration
- **Settings**: `src/config.py`
    - `pydantic-settings` を使用した設定管理。
    - `.env.local` から環境変数を自動読み込み。

### 2.1 Infrastructure Layer
- **Client**: `src/infrastructure/dynamodb/client.py`
    - `src.config.get_settings()` を使用して接続設定を取得。
- **Converters**: `src/infrastructure/dynamodb/converters.py`
    - Domain Model <-> DynamoDB Item の相互変換。
- **Repository**: `src/infrastructure/dynamodb/mock_repository.py`
    - `DynamoMockRepository` クラス。
    - Single Table Design を採用。
    - `MockRepository` Protocol (Domain Layer) に準拠。

### 2.2 Database Schema (Single Table Design)
- **Table Name**: `MockTable`
- **Partition Key (PK)**: `MOCK#{method}#{path}` (例: `MOCK#GET#/users/1`)
- **Sort Key (SK)**: `METADATA` (固定)
- **GSI**: `GSI-ID`
    - PK: `GSI1PK` (Mock ID)
    - 用途: IDによる検索・削除

### 2.3 Scripts
- **Initialization**: `scripts/init_dynamodb.py`
    - ローカル開発用に `MockTable` を作成するスクリプト。

## 3. Phase 4 (Interface & Integration) に向けた準備

### 3.1 必要な環境変数
`pydantic-settings` を導入したため、ローカル開発時は `.env.local` ファイルで管理します。
`src/config.py` がこのファイルを自動的に読み込みます。

**`.env.local` (作成済み)**:
```ini
DYNAMODB_ENDPOINT_URL="http://db:8000"
AWS_DEFAULT_REGION="us-east-1"
AWS_ACCESS_KEY_ID="dummy"
AWS_SECRET_ACCESS_KEY="dummy"
LOG_LEVEL="INFO"
```

### 3.2 依存関係注入 (Dependency Injection)
`src/dependencies.py` にて、`DynamoMockRepository` を初期化し、Service に注入する設定が必要です。

```python
# src/dependencies.py のイメージ
from src.infrastructure.dynamodb.mock_repository import DynamoMockRepository

def get_repository() -> MockRepository:
    return DynamoMockRepository(table_name="MockTable")
```

### 3.3 API Router 実装方針
- **Management API**: `src/domain/mocks/router.py`
    - `MockManagementService` を使用。
    - エラーハンドリングは `Result` 型の `match` 文で行う。
- **Simulation API**: `src/main.py` (または専用Router)
    - Catch-all ルート `/{path:path}` を定義。
    - `MockSimulatorService` を使用。
    - 最も優先度が低くなるように最後に include する。

## 4. テスト実行方法

### 統合テスト (Repository)
DynamoDB Local が起動している必要があります。

```bash
# テスト実行
uv run pytest tests/integration/test_dynamodb_repository.py
```

### DB初期化 (ローカル実行用)
```bash
python3 scripts/init_dynamodb.py
```
