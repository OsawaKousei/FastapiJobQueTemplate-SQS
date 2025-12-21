# **FastAPI Strict Guideline** 

**Extension of Minimal Python Guideline**

## **1\. 基本方針 (Core Philosophy)**

本規約は「Minimal Python Guideline」を継承し、FastAPIを用いたバックエンド開発におけるアーキテクチャ、データフロー、品質管理の標準を定める。

### **1.1 FastAPI as an Interface**

FastAPI（およびその機能である Depends, HTTPException 等）は、あくまで「HTTPインターフェース層」でのみ使用する。  
ビジネスロジック（Service層）が FastAPI に依存してはならない。

### **1.2 Explicit Dependency**

グローバルステート（モジュールレベルの変数）を禁止し、すべての依存関係（設定、DB接続、外部クライアント）は Dependency Injection (DI) によって解決する。

## ---

**2\. アーキテクチャとレイヤー (Architecture & Layers)**

アプリケーションを以下の3層に厳格に分離する。依存の方向は **Router \-\> Service \-\> Repository** の一方通行とする。

| Layer | Component | Role | Input | Output |
| :---- | :---- | :---- | :---- | :---- |
| **Interface** | Router | HTTPリクエストの受付、Serviceの呼び出し、レスポンス変換 | Pydantic (Schema) | JSON / HTTP Status |
| **Domain** | Service | ビジネスロジック、計算、判定 | Domain Model | Result\[T, Error\] |
| **Infrastructure** | Repository | データの永続化、外部API通信 | Domain Model | Domain Model |

### **2.1 Router (Controller)**

* **責務:** 入力のバリデーション（Pydantic）、Serviceの実行、結果のHTTPレスポンスへのマッピング。  
* **禁止:** 条件分岐や計算などのロジック記述。

### **2.2 Service (Domain Logic)**

* **責務:** アプリケーションの核心となるロジック。  
* **特徴:** 純粋な Python クラス。FastAPI、DBドライバ、HTTPクライアントに依存しない。  
* **禁止:** HTTPException の送出（Result型を返すこと）。

### **2.3 Repository (Persistence)**

* **責務:** データの取得と保存。  
* **特徴:** Protocol として抽象化され、実装詳細（SQLAlchemy, Redis等）を隠蔽する。

## ---

**3\. データモデルとスキーマ (Data Models & Schemas)**

「Immutable Data Models 」に基づき、データの用途に応じて厳密にクラスを分ける。

### **3.1 Schema Strategy (入力と出力の分離)**

1つのモデルを使い回すことを禁止し、ユースケースごとに定義する。

* **Input Schema:** リクエスト受け取り用。バリデーションロジック (@field\_validator) を含む。  
* **Output Schema:** レスポンス返却用。ドメインモデルから生成する。  
* **Domain Model:** アプリケーション内部で回すデータ。

### **3.2 ORM Model Isolation**

* **ルール:** SQLAlchemy等のORMモデル（可変オブジェクト）は、**Repositoryの内部のみ**に生存期間を限定する。  
* Repositoryは必ず orm\_model \-\> pydantic\_model の変換を行ってから値を返すこと。

## ---

**4\. エラーハンドリング (Error Handling)**

「ネイティブ Result パターンの採用 」をWeb APIに適用する。

### **4.1 Service Layer**

例外 (raise) を使用せず、Result 型（Union型）を返す。

Python

\# domain/users/service.py  
class UserService:  
    def get\_user(self, uid: str) \-\> User | ResourceNotFoundError:  
        user \= self.repo.find(uid)  
        if user is None:  
            return ResourceNotFoundError(f"User {uid} not found")  
        return user

### **4.2 Router Layer**

Serviceから返された Result を match 文でハンドリングし、適切なHTTPステータスに変換する。

Python

\# domain/users/router.py  
@router.get("/{uid}")  
async def get\_user\_endpoint(  
    uid: str,   
    service: Annotated\[UserService, Depends(get\_user\_service)\]  
):  
    result \= service.get\_user(uid)  
    match result:  
        case User() as user:  
            return UserResponse.model\_validate(user)  
        case ResourceNotFoundError() as e:  
            raise HTTPException(status\_code=404, detail=e.message)  
        case \_:  
            raise HTTPException(status\_code=500, detail="Internal Server Error")

## ---

**5\. データベースと永続化 (Persistence)**

「Protocol による抽象化 」を適用し、特定のDB技術へのロックインを防ぐ。

### **5.1 Repository Protocol**

Serviceは必ずインターフェース（Protocol）に依存する。

Python

\# domain/users/repository.py (Interface)  
class UserRepository(Protocol):  
    async def save(self, user: User) \-\> User: ...

### **5.2 Implementation (Dependency Injection)**

具体的な実装（PostgreSQL等）は main.py や dependencies.py で注入する。

Python

\# infrastructure/persistence/postgres\_repo.py  
class PostgresUserRepository:  
    def \_\_init\_\_(self, session: AsyncSession):  
        self.\_session \= session  
    \# ...実装...

## ---

**6\. ロギング (Logging)**

「宣言的記述 」と「構造化ログ」を採用する。

### **6.1 Logging Strategy**

* **Structured Logs:** 本番環境ではJSON形式で出力し、機械可読性を担保する。  
* **Context Aware:** ContextVar を使用し、すべてのログに request\_id を自動付与する。

### **6.2 Configuration (logging\_config.yaml)**

コード内に設定を書かず、外部ファイルで定義する。

YAML

version: 1  
formatters:  
  json:  
    class: pythonjsonlogger.jsonlogger.JsonFormatter  
    format: "%(asctime)s %(levelname)s %(name)s %(message)s %(request\_id)s"  
handlers:  
  console:  
    class: logging.StreamHandler  
    formatter: json  
loggers:  
  app:  
    level: INFO  
    handlers: \[console\]

## ---

**7\. テスト規約 (Testing Strategy)**

テスト容易性を活かし、ピラミッド型のテスト戦略をとる。

### **7.1 Unit Test (Domain Logic)**

* **対象:** Service, Schema, Utility.  
* **方針:** **Solitary (孤独な) テスト**。  
* **ルール:** Repository等の依存はすべて Mock または Fake に差し替え、IOを発生させない。

### **7.2 Integration Test (API)**

* **対象:** Router (End-to-Endに近い検証).  
* **方針:** **Sociable (社交的な) テスト**。  
* **ツール:** TestClient (AsyncClient) \+ Testcontainers (またはトランザクションロールバック).  
* **ルール:** Service層はモックせず、実際のDBプロセスを用いてデータの整合性を検証する。外部APIのみ app.dependency\_overrides でモック化する。

### **7.3 Data Generation**

* **ツール:** polyfactory を使用。  
* **ルール:** 巨大な辞書やコンストラクタを手書きせず、Factoryで生成する。

## ---

**8\. ディレクトリ構造 (Directory Structure)**

「機能単位の構造 (Feature-based Structure) 」を拡張する。

Plaintext

src/  
  domain/                 \# ビジネスドメインごとの分割  
    users/  
      \_\_init\_\_.py  
      router.py           \# Endpoint definition  
      services.py         \# Business Logic (Pure Python)  
      schemas.py          \# Input/Output Pydantic Models  
      repository.py       \# Repository Interface (Protocol)  
      exceptions.py       \# Domain Errors (Result types)  
  infrastructure/         \# 技術的詳細の実装  
    persistence/  
      postgres/           \# Concrete Repository Implementations  
      redis/  
    external/             \# External API Clients  
  shared/                 \# 共通コンポーネント  
    logging\_utils.py      \# Request ID filter, etc.  
    result.py             \# Result Monad definition  
  main.py                 \# App definition & DI wiring

## ---

**9\. ツール設定 (Tooling)**

「強制と自動化 」のため、以下の設定を必須とする。

* **Ruff:** pyproject.toml にてルールを厳格化（使用禁止構文の物理的排除）。  
* **Mypy:** disallow\_any\_generics \= true, strict \= true.