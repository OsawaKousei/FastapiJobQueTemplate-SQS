# **FastAPI Strict Guideline: Testing Strategy**

**Extension of FastAPI Strict Guideline (Section 7\)**

## **1\. テスト基本方針 (Core Philosophy)**

本プロジェクトでは、「Minimal」かつ「Explicit」なテストコードを維持するため、**pytest エコシステムのみ**を採用する。

### **1.1 Pure Python Testing**

* **No Magic:** unittest.mock や @patch デコレータによる「黒魔術的な」書き換えを原則禁止する。  
* **Explicit DI:** テスト対象への依存注入は、コンストラクタ経由で明示的に行う。  
* **Fake over Mock:** 依存関係の代替には、モックライブラリではなく\*\*「Fake（偽装クラス）」\*\*の使用を第一選択とする。

### **1.2 Testing Pyramid Strategy**

| Type | Target | Scope | Dependencies | Strategy |
| :---- | :---- | :---- | :---- | :---- |
| **Unit** | Service / Domain | **Solitary** | **Fake Implementation** | ロジックの網羅的検証。DBレスで高速に実行。 |
| **Integration** | Router / API | **Sociable** | **Real DB / Docker** | エンドツーエンドの結合検証。外部APIのみMock化。 |

## **\---**

## **2\. 技術スタック (Tech Stack)**

unittest 標準ライブラリの使用を禁止し、以下のライブラリ群で統一する。

* **Runner:** pytest  
* **Async Support:** pytest-asyncio (asyncio\_mode \= "auto")  
* **HTTP Client:** httpx (Starlette/FastAPI標準の AsyncClient 利用)  
* **Data Factory:** polyfactory (Pydanticモデルからのデータ生成)  
* **Coverage:** pytest-cov  
* **Mocking (Restricted):** pytest-mock  
  * *注:* datetime.now() の固定や、Fake作成が困難なサードパーティライブラリの制御にのみ限定的に使用する（mocker fixture経由）。unittest.mock の直接インポートは禁止。

## **\---**

## **3\. ディレクトリ構造 (Directory Structure)**

テストコードも「関心の分離」に従い、Unit（Solitary）とIntegration（Sociable）を物理的に分離する。

Plaintext

tests/  
  ├── conftest.py             \# 全体共通のFixture (DB接続, AsyncClient等)  
  ├── fakes/                  \# 再利用可能なFakeクラス群  
  │   ├── \_\_init\_\_.py  
  │   └── fake\_user\_repo.py  
  ├── unit/                   \# Unit Tests (DB不要・高速)  
  │   └── domain/  
  │       └── users/  
  │           └── test\_user\_service.py  
  └── integration/            \# Integration Tests (DB必要・低速)  
      └── api/  
          └── users/  
              └── test\_user\_router.py

## **\---**

## **4\. Unit Test 戦略 (The Fake Pattern)**

Service層のテストでは、RepositoryのProtocolに基づいて、Pythonの辞書（Dict）等を使った単純なクラス（Fake）を作成・注入する。

### **4.1 Fakeの実装 (in tests/fakes/)**

ロジックを持たず、単純な入出力のみを行うこと。

Python

\# tests/fakes/fake\_user\_repo.py  
from src.domain.users.repository import UserRepository  
from src.domain.users.schemas import User

class FakeUserRepository(UserRepository):  
    def \_\_init\_\_(self):  
        self.\_storage: dict\[str, User\] \= {}

    async def save(self, user: User) \-\> User:  
        self.\_storage\[user.id\] \= user  
        return user

    async def find(self, uid: str) \-\> User | None:  
        return self.\_storage.get(uid)

### **4.2 テストケースの実装 (in tests/unit/)**

unittest.mock を使わず、コンストラクタインジェクションで依存を解決する。

Python

\# tests/unit/domain/users/test\_user\_service.py  
import pytest  
from src.domain.users.service import UserService  
from src.shared.result import ResourceNotFoundError  
from tests.fakes.fake\_user\_repo import FakeUserRepository  
from polyfactory.factories.pydantic\_factory import ModelFactory  
from src.domain.users.schemas import User

\# Factory定義（テストファイル内に配置可）  
class UserFactory(ModelFactory\[User\]):  
    \_\_model\_\_ \= User

@pytest.mark.asyncio  
async def test\_get\_user\_returns\_user\_when\_found():  
    \# Arrange: Fakeを準備し、データを仕込む  
    fake\_repo \= FakeUserRepository()  
    existing\_user \= UserFactory.build(id\="user\_123")  
    await fake\_repo.save(existing\_user)

    \# Act: ServiceにFakeを注入  
    service \= UserService(repo=fake\_repo)  
    result \= await service.get\_user("user\_123")

    \# Assert: Result型の正常系を検証  
    assert result \== existing\_user

@pytest.mark.asyncio  
async def test\_get\_user\_returns\_error\_when\_missing():  
    \# Arrange: 空のFake  
    fake\_repo \= FakeUserRepository()  
    service \= UserService(repo=fake\_repo)

    \# Act  
    result \= await service.get\_user("non\_existent")

    \# Assert: Result型の異常系を検証  
    assert isinstance(result, ResourceNotFoundError)

## **\---**

## **5\. Integration Test 戦略 (The Sociable Pattern)**

Routerのテストでは、実際のDB（Docker等）を使用し、アプリ全体 (main.app) を通してリクエストを送る。

### **5.1 外部APIのモック化 (dependency\_overrides)**

外部システム（SaaS等）への通信のみ、FastAPIの機能を使って無効化する。

Python

\# tests/conftest.py (抜粋)  
import pytest\_asyncio  
from httpx import AsyncClient  
from main import app  
from src.infrastructure.external.email\_client import EmailClient

\# 外部クライアントのFake  
class FakeEmailClient:  
    async def send(self, to: str, body: str):  
        pass  \# 何もしない

@pytest\_asyncio.fixture  
async def async\_client():  
    \# 外部依存のみ差し替え  
    app.dependency\_overrides\[EmailClient\] \= FakeEmailClient  
      
    async with AsyncClient(app=app, base\_url="http://test") as client:  
        yield client  
      
    \# クリーンアップ  
    app.dependency\_overrides.clear()

### **5.2 Routerテストの実装**

Python

\# tests/integration/api/users/test\_user\_router.py  
import pytest  
from src.domain.users.schemas import UserResponse

@pytest.mark.asyncio  
async def test\_get\_user\_endpoint\_200(async\_client, db\_session):  
    \# Arrange: DBに直接データ投入 (またはFactory経由でRepository使用)  
    \# ここでは統合テスト用FixtureがDBをセットアップ済みと仮定  
    ... 

    \# Act  
    response \= await async\_client.get("/users/user\_123")

    \# Assert  
    assert response.status\_code \== 200  
    assert UserResponse.model\_validate(response.json())

## **\---**

## **6\. データ生成 (Data Generation)**

テストデータの作成に巨大な辞書リテラルや、長いコンストラクタ呼び出しを使用することを禁止する。必ず polyfactory を使用する。

* **理由:** スキーマ変更時の修正コストを下げるため。  
* **使用法:** 必要なフィールドのみ build() メソッドで上書きする。

Python

\# BAD  
user \= User(id\="1", name="Test", email="test@example.com", age=20, is\_active=True, ...)

\# GOOD  
user \= UserFactory.build(id\="1", name="Test") \# 他のフィールドはランダム自動生成

## **\---**

## **7\. 設定ファイル (pyproject.toml)**

カバレッジ計測と非同期設定を強制する。

Ini, TOML

\[tool.pytest.ini\_options\]  
testpaths \= \["tests"\]  
python\_files \= "test\_\*.py"  
addopts \= "-ra \-q \--cov=src \--cov-report=term-missing \--strict-markers"  
asyncio\_mode \= "auto"

\[tool.coverage.run\]  
branch \= true  
omit \= \[  
    "src/main.py",  
    "src/\*\*/protocol.py"  
\]

\[tool.coverage.report\]  
\# テストカバレッジが低い場合に失敗させる（閾値はプロジェクト状況に合わせる）  
fail\_under \= 80  
show\_missing \= true  
