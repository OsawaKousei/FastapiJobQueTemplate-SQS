[](file:///home/kousei/WebDev/FastapiJobQueTemplate-SQS/common/domain/job_a/job_schemas.py) の読み取り

[](file:///home/kousei/WebDev/FastapiJobQueTemplate-SQS/worker/app/src/domain/job_a/service.py) の読み取り

[](file:///home/kousei/WebDev/FastapiJobQueTemplate-SQS/backend/app/src/domain/api_a/schemas.py) の読み取り

[](file:///home/kousei/WebDev/FastapiJobQueTemplate-SQS/common/domain/job_b/job_schemas.py) の読み取り

[](file:///home/kousei/WebDev/FastapiJobQueTemplate-SQS/worker/app/src/domain/job_b/service.py) の読み取り

[](file:///home/kousei/WebDev/FastapiJobQueTemplate-SQS/backend/app/src/domain/api_b/schemas.py) の読み取り

[](file:///home/kousei/WebDev/FastapiJobQueTemplate-SQS/common/domain/job_c/job_schemas.py) の読み取り

[](file:///home/kousei/WebDev/FastapiJobQueTemplate-SQS/worker/app/src/domain/job_c/service.py) の読み取り

[](file:///home/kousei/WebDev/FastapiJobQueTemplate-SQS/backend/app/src/domain/api_c/schemas.py) の読み取り

このリポジトリには現在、以下の3つのサンプルジョブが実装されています。
それぞれの役割と、API(入力)・Worker(内部処理)・Result(出力)の関係を整理します。

### 1. Job A: テキスト処理 (Message Processing)

最も基本的な「文字列を受け取って加工して返す」ジョブのサンプルです。

- **API (Input)**
  - **Endpoint**: `POST /api/v1/a`
  - **Request Schema**:
    - `text` (str): 処理対象のメッセージ
    - `priority` (int): 優先度 (1-5, 現在はロジック未使用)
- **Worker Logic**
  - **Service**: `JobAService`
  - **Payload**: `JobAPayload(message: str)`
  - **Process**: 単純にスリープ(1秒)し、メッセージの先頭に `"Processed Job A: "` を付与する。
- **Result (Output)**
  - **Response Schema**:
    - `text` (str): 元のメッセージ
    - `processed_message` (str): 加工後のメッセージ
    - `status`: 処理状態

---

### 2. Job B: 数値計算 (Number Calculation)

数値を受け取って計算処理を行うジョブのサンプルです。CPUバウンドな処理のシミュレーションと見なせます。

- **API (Input)**
  - **Endpoint**: `POST /api/v1/b`
  - **Request Schema**:
    - `length` (int): 数値 (ソースコード上の変数名は `length` だが、Payloadへは `count` として渡される)
- **Worker Logic**
  - **Service**: `JobBService`
  - **Payload**: `JobBPayload(count: int)`
  - **Process**: スリープ(2秒)し、入力数値を **二乗 (n^2)** する。
- **Result (Output)**
  - **Response Schema**:
    - `squared_result` (int):計算結果

---

### 3. Job C: リスト処理 (List Processing)

リスト（配列）データを受け取り、集計やフィルタリングを行うジョブのサンプルです。

- **API (Input)**
  - **Endpoint**: `POST /api/v1/c`
  - **Request Schema**:
    - `raw_tags` (str): カンマ区切りの文字列 (例: `"python, fastAPI, aws"`)
- **Worker Logic**
  - **Service**: `JobCService`
  - **Payload**: `JobCPayload(tags: List[str])`
  - **Process**:
    - API側でカンマ区切り文字列をリストに変換してからPayloadを作成。
    - Workerはスリープ(3秒)し、リストの要素数(`tag_count`)をカウントする。
- **Result (Output)**
  - **Response Schema**:
    - `tag_count` (int): タグの個数
    - `tags` (List[str]): 処理されたタグのリスト

---

### まとめ

| Feature   | エンドポイント | 入力 (API)        | 主な処理 (Worker)              | 出力 (Result)       | 想定されるユースケース                  |
| :-------- | :------------- | :---------------- | :----------------------------- | :------------------ | :-------------------------------------- |
| **Job A** | `/api/v1/a`    | `text` (Message)  | 文字列加工 (Wait 1s)           | `processed_message` | メール送信、通知、テキスト解析          |
| **Job B** | `/api/v1/b`    | `length` (Number) | 二乗計算 (Wait 2s)             | `squared_result`    | 科学技術計算、レポート生成              |
| **Job C** | `/api/v1/c`    | `raw_tags` (CSV)  | リスト変換・カウント (Wait 3s) | `tag_count`, `tags` | データ（CSV/Excel）インポート、一括処理 |
