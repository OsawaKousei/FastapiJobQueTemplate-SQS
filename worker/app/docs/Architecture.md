# アーキテクチャ設計とディレクトリ構造

## 1. 設計コンセプト

このレポジトリは、**バックエンド（API）**と**非同期ワーカー**という2つの異なるランタイムが、**同一のドメインロジックとインフラストラクチャコード**を共有して動作することを前提としています。

### コア・プリンシプル
1.  **Common Core (共有コア)**: ビジネスロジック、DB操作、データ定義は `common/` に集約し、APIとワーカーの両方から参照可能にする。
2.  **Interface Segregation (インターフェース分離)**:
    *   **API (`src/`)**: HTTPリクエストを受け付け、即座に応答するためのインターフェース。
    *   **Worker**: キューからのメッセージを受け付け、長時間かかる処理を行うためのインターフェース。
3.  **Docker Volume Sharing**: 開発時は `common/` ディレクトリを各コンテナにマウントすることで、コードの二重管理を防ぐ。

## 2. ディレクトリ構造詳細

```plaintext
/app
├── common/                  # 【共有領域】APIとWorkerの両方で使用
│   ├── config.py            # 環境設定
│   ├── jobs/                # ドメイン: ジョブ管理機能
│   │   ├── services.py      # JobService (API用: ジョブ登録・参照)
│   │   ├── processor.py     # JobProcessor (Worker用: ジョブ実行エンジン)
│   │   ├── repository.py    # データアクセスインターフェース (Protocol)
│   │   ├── queue.py         # キュー操作インターフェース (Protocol)
│   │   └── schemas.py       # データモデル (Pydantic)
│   ├── infrastructure/      # インフラ実装 (AWS DynamoDB, SQS等)
│   └── shared/              # 共通ユーティリティ (Logging, Result型)
│
├── src/                     # 【API領域】バックエンドサーバー専用
│   ├── main.py              # FastAPI エントリーポイント
│   ├── dependencies.py      # DIコンテナ (commonのクラスを組み立てる)
│   └── domain/
│       └── jobs/
│           └── router.py    # HTTPルーティング (FastAPI依存)
│
└── (worker/)                # 【Worker領域】(今後作成)
    └── main.py              # Worker エントリーポイント
```

### 各ディレクトリの役割

*   **`common/`**:
    *   **純粋なPythonコード**で構成され、Webフレームワーク（FastAPI）への依存を持ちません。
    *   ここに定義された `Service` や `Repository` は、APIからもWorkerからも全く同じように呼び出されます。
*   **`src/`**:
    *   **HTTP通信の制御**に特化しています。
    *   `router.py` は `common` の `JobService` を呼び出し、結果をHTTPレスポンスに変換する「アダプター」の役割を果たします。
    *   `domain/jobs/router.py` という配置により、機能単位の構造（Feature-based）を維持しています。

## 3. バックエンドとワーカーの差異と共有

| 特徴 | バックエンド (API) | ワーカー (Worker) |
| :--- | :--- | :--- |
| **主な責務** | ジョブの受付(登録)、ステータス照会 | ジョブの実処理、結果の保存 |
| **トリガー** | HTTPリクエスト (User -> API) | SQSメッセージ (Queue -> Worker) |
| **使用するロジック** | `common.jobs.services.JobService`<br>(create_job, get_job) | `common.jobs.processor.JobProcessor`<br>(process_next) |
| **依存関係** | FastAPI, Uvicorn | (なし / ループ処理のみ) |
| **共有するもの** | **Repository (DB接続), Queue (SQS接続), Schemas (データ型), Config** | (左記と同じ) |

### 処理の流れ

1.  **API (src)**:
    *   ユーザーが `POST /jobs` を叩く。
    *   `src/domain/jobs/router.py` が `common.jobs.services.JobService` を呼ぶ。
    *   `JobService` が DBに保存し、SQSにIDを送信する。
2.  **Worker**:
    *   常駐プロセスが `common.jobs.processor.JobProcessor` をループ実行。
    *   SQSからメッセージを受信。
    *   `JobProcessor` に注入された**ハンドラ関数**を実行し、結果をDBに更新する。

この構造により、**「処理ロジックを変えたいときは `common` だけを修正すれば、APIとワーカーの両方に反映される」**という保守性の高い状態を実現しています。
