# **Serverless Mock API Generator 開発仕様書**

## **1\. プロジェクト概要**

### **1.1 目的**

フロントエンド開発や外部連携テストのために、指定したレスポンスを返す「モックAPIエンドポイント」を動的に作成・管理するツール。  
サーバーレスアーキテクチャ（AWS Lambda \+ DynamoDB）を採用し、低コストかつスケーラブルに運用する。

### **1.2 技術スタック**

* **Interface:** FastAPI, Uvicorn  
* **Runtime:** AWS Lambda Web Adapter (Docker)  
* **Language:** Python 3.11+  
* **Logic:** Pydantic (Strict Data Models), Result Pattern (dry-python/returns or Simple Union)  
* **Persistence:** DynamoDB (Single Table Design)  
* **IaC:** AWS SAM or Terraform

## ---

**2\. ドメインモデル設計 (Immutable Data Models)**

アプリケーションの核となるデータ構造です。frozen=True を徹底し、状態変更は複製（Copy & Update）によって行います。

### **2.1 Value Objects (Enums & Types)**

Python

from enum import StrEnum

class HttpMethod(StrEnum):  
    GET \= "GET"  
    POST \= "POST"  
    PUT \= "PUT"  
    DELETE \= "DELETE"  
    PATCH \= "PATCH"

class ContentType(StrEnum):  
    JSON \= "application/json"  
    TEXT \= "text/plain"  
    HTML \= "text/html"

### **2.2 Entities (Schemas)**

Python

from pydantic import BaseModel, ConfigDict, Field, HttpUrl  
from typing import Any

class MockEndpoint(BaseModel):  
    """  
    1つのモックエンドポイント定義。  
    不変オブジェクトとして扱う。  
    """  
    model\_config \= ConfigDict(frozen=True)

    id: str \= Field(..., description="UUID")  
    path: str \= Field(..., description="/users/123 などのパス")  
    method: HttpMethod  
    status\_code: int \= Field(200, ge=100, le=599)  
    response\_body: dict\[str, Any\] | str \= Field(default\_factory=dict)  
    headers: dict\[str, str\] \= Field(default\_factory=dict)  
    latency\_ms: int \= Field(0, ge=0, description="シミュレートする遅延時間(ms)")  
      
    @property  
    def key(self) \-\> str:  
        """ユニークキー: メソッドとパスの組み合わせ"""  
        return f"{self.method}:{self.path}"

class MockTemplateContext(BaseModel):  
    """レスポンス生成時の動的置換用コンテキスト"""  
    model\_config \= ConfigDict(frozen=True)  
    request\_id: str  
    timestamp: str

## ---

**3\. アーキテクチャ構成**

### **3.1 3層構造の責務**

| Layer | Component | Role |
| :---- | :---- | :---- |
| **Interface** | Router | **Management API**（モックの登録・削除）と **Simulation API**（実際にモックとして振る舞う）の2つの顔を持つ。 |
| **Domain** | Service | モックの検索、テンプレート処理（{{uuid}}等の置換）、遅延シミュレーション（asyncio.sleep）。 |
| **Infrastructure** | Repository | DynamoDBへの保存・取得。PK設計による高速なルックアップ。 |

### **3.2 ディレクトリ構造 (Feature-based)**

Plaintext

src/  
  domain/  
    mocks/  
      \_\_init\_\_.py  
      schemas.py        \# Data Models  
      service.py        \# MockManagementService, MockSimulatorService  
      repository.py     \# Protocol Definition  
      router.py         \# Endpoints  
      template\_engine.py \# 簡易テンプレート置換ロジック  
  infrastructure/  
    dynamodb/  
      mock\_repository.py \# Concrete Implementation  
  main.py

## ---

**4\. 機能詳細とロジック**

### **4.1 モック管理機能 (Management)**

* **API:**  
  * POST /api/mocks: モックの新規登録  
  * GET /api/mocks: 一覧取得  
  * DELETE /api/mocks/{mock\_id}: 削除  
* **バリデーション:**  
  * path は必ず / で始まること。  
  * response\_body が JSON の場合、構文が正しいこと。

### **4.2 モックシミュレーション機能 (Simulation)**

ここがシステムの心臓部です。FastAPIの **Catch-all path** を利用します。

* **API:** Any /{path:path} (全てのリクエストを受け止める)  
* **Service Logic (MockSimulatorService):**  
  1. **Lookup:** リクエストされた method と path をキーに、Repositoryから MockEndpoint を検索する。  
  2. **Not Found Handling:** 登録がない場合、Serviceは Result.Failure(NotFoundError) を返す（Routerで404に変換）。  
  3. **Latency Simulation:** MockEndpoint.latency\_ms \> 0 ならば、await asyncio.sleep(ms / 1000\) を実行。**（これはIOバウンド操作なのでasyncで書く）**  
  4. **Template Processing:** レスポンスボディ内のプレースホルダーを置換する（例: {{random.uuid}} → 550e8400...）。  
  5. **Return:** ステータスコード、ヘッダー、ボディを含む結果オブジェクトを返す。

### **4.3 テンプレートエンジン (Template Engine)**

簡易的な置換ロジックを実装します。

* **仕様:** 文字列置換のみ対応。  
* **対応タグ:**  
  * {{uuid}}: ランダムなUUIDv4  
  * {{now\_iso}}: 現在時刻 (ISO8601)  
  * {{random\_int}}: 0-100のランダム整数

## ---

**5\. データベース設計 (DynamoDB)**

Single Table Designを採用します。検索速度（Simulation時のルックアップ）を最優先します。

* **Table Name:** MockTable (環境変数で注入)  
* **Partition Key (PK):** MOCK\#{method}\#{path}  
  * 例: MOCK\#GET\#/users/123  
  * 理由: シミュレーション時、パスとメソッドは既知であるため、GetItem (O(1)) で高速に特定できる。  
* **Sort Key (SK):** METADATA (固定)  
  * 将来的に履歴管理などをする場合はタイムスタンプにするが、V1では固定で良い。

| PK | SK | Attribute: payload (JSON) | Attribute: ttl |
| :---- | :---- | :---- | :---- |
| MOCK\#GET\#/users/1 | METADATA | { "id": "...", "status": 200, ... } | 1735689600 |

## ---

**6\. API定義 (Interface Layer)**

### **6.1 Management Router**

Python

\# src/domain/mocks/router.py

@router.post("/api/mocks", status\_code=201)  
async def create\_mock(  
    schema: CreateMockSchema,  
    service: Annotated\[MockManagementService, Depends(get\_mock\_mgmt\_service)\]  
) \-\> MockEndpointResponse:  
    \# Serviceは Result型 を返す  
    result \= await service.register(schema)  
    match result:  
        case Success(mock):  
            return MockEndpointResponse.model\_validate(mock)  
        case Failure(e):  
            raise HTTPException(status\_code=400, detail=str(e))

### **6.2 Simulation Router (The Catch-all)**

このルーターは、他のすべてのルーター定義の**最後**に配置する必要があります。

Python

\# src/main.py または専用router

@router.api\_route("/{path:path}", methods=\["GET", "POST", "PUT", "DELETE", "PATCH"\])  
async def handle\_simulation(  
    request: Request,  
    path: str,  
    service: Annotated\[MockSimulatorService, Depends(get\_mock\_sim\_service)\]  
):  
    \# 1\. 検索用キーの構築  
    method \= request.method  
    full\_path \= f"/{path}" \# FastAPIは先頭の/を除くため付与  
      
    \# 2\. 実行  
    result \= await service.execute(method, full\_path)  
      
    \# 3\. レスポンス構築  
    match result:  
        case Success(sim\_result):  
            return JSONResponse(  
                content=sim\_result.body,  
                status\_code=sim\_result.status\_code,  
                headers=sim\_result.headers  
            )  
        case Failure(NotFoundError()):  
            \# モック未定義時は404を返す  
            raise HTTPException(status\_code=404, detail="Mock not found")

## ---

**7\. 開発ステップ**

1. **Coreの実装:**  
   * schemas.py で MockEndpoint を定義。  
   * template\_engine.py で置換ロジックをTDD（テスト駆動）で実装。  
2. **Serviceの実装 (In-Memory):**  
   * repository.py のProtocolを定義。  
   * InMemoryMockRepository を作り、DBなしで登録→シミュレーションの流れを実装・テストする。  
3. **Interfaceの実装:**  
   * FastAPIのRouterを実装し、ローカルサーバー(Uvicorn)で動作確認。  
4. **Infrastructureの実装:**  
   * DynamoDB (boto3) を実装した DynamoMockRepository を作成。  
   * docker-compose で dynamodb-local を立てて結合テスト。  
5. **AWS Deployment:**  
   * Dockerfile.prod (Lambda Adapter) の作成。  
   * SAM または CDK でインフラ定義とデプロイ。

---

この仕様書に基づき、まずは **「Core (Schemas) の定義」** と **「Template Engine の単体テスト」** から着手するのが良いでしょう。この部分は完全にピュアなPythonコードで書けるため、プロジェクトの立ち上げとして最適です。