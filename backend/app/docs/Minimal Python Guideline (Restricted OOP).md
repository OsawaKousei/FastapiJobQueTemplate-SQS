# **Minimal Python Guideline (Restricted OOP)**

# **1\. 基本原則 (Core Principles)**

## **1.1 Stateless OOP (ステートレスなオブジェクト指向)**

定義: クラスは「データの定義」か「依存解決の単位（名前空間）」のいずれかであり、状態を持つロジック（ステートフルなオブジェクト）は作成しない。  
適用:

* インスタンス変数（self.value）をメソッド内で書き換える行為（Mutation）を禁止する。  
* クラスは、初期化時（\_\_init\_\_）に依存関係（他のサービスや設定）を受け取るためだけに存在し、メソッド呼び出しによって内部状態が変わってはならない。

## **1.2 Composition over Inheritance (継承より合成)**

定義: コードの再利用を目的とした「実装継承」を禁止する。  
適用:

* class Child(Parent): のような継承は、親クラスの変更が子クラスに予期せぬ影響を与える（Fragile Base Class Problem）ため禁止する。  
* 共通ロジックが必要な場合は、別のオブジェクトとして切り出し、コンポジション（メンバ変数として保持）によって利用する。  
* 例外として、型定義 (Pydantic, Dataclasses) やインターフェース定義 (typing.Protocol) の継承のみ許可する。

## **1.3 Immutable Data Models (不変データモデル)**

定義: アプリケーション内で扱うデータは、作成された瞬間から不変（Immutable）である。  
適用:

* データ保持用のオブジェクトはすべて frozen=True とする。  
* データの変更が必要な場合は、既存の値を変更するのではなく、複製して新しい値を生成（Copy & Update）する。

## **1.4 Declarative over Imperative (宣言的記述の優先)**

定義: 「どのように（How）」処理するかではなく、「何が欲しいか（What）」を記述する。  
適用:

* 手続き的なループ（for 文による空リストへの append）は、ロジックの流れを追うコストが高いため禁止する。  
* データ変換には必ず「リスト内包表記」または「高階関数」を使用し、副作用を排除する。

# **2\. クラスの分類と役割 (Class Taxonomy)**

Pythonにおけるクラスの使用を、以下の2種類に厳格に限定します。これらの中間的な「データもロジックも持つクラス」は作成しません。

## **2.1 Data Object (Schema)**

データのみを保持し、振る舞い（副作用のあるメソッド）を持たないクラス。

* **役割:** ドメインデータの定義、バリデーション。  
* **実装:** Pydantic BaseModel (推奨) または dataclasses。  
* **ルール:**  
  * 必ず frozen=True を設定し、不変にする。  
  * メソッドは「算出プロパティ（Computed Field）」や「自己完結した変換ロジック」のみ許可し、外部IOや状態変更は禁止する。

Python

\# ✅ Good  
class UserProfile(BaseModel):  
    model\_config \= ConfigDict(frozen=True)  
    id: str  
    name: str

## **2.2 Service Object (Operation)**

振る舞いのみを持ち、状態（可変データ）を持たないクラス。

* **役割:** ビジネスロジックの実行、計算、オーケストレーション。  
* **実装:** 通常の Python クラス。  
* **ルール:**  
  * \_\_init\_\_ では「他のサービス」や「定数設定」のみを受け取り、保持する。  
  * メソッドはすべて純粋関数、またはIOを伴うコマンドとして設計する。  
  * メソッドの引数と戻り値は、必ず **Data Object** またはプリミティブ型とする。

Python

\# ✅ Good  
class UserService:  
    def \_\_init\_\_(self, repository: UserRepository):  
        self.\_repository \= repository \# 依存関係の注入のみ

    def register(self, user: UserProfile) \-\> Result\[UserProfile, Error\]:  
        \# selfの状態は変更しない  
        return self.\_repository.save(user)

# **3\. 禁止・制限される構文 (Restricted Syntax)**

可読性を損なう、またはバグの温床となる構文を物理的に禁止します。

## **3.1 手続き的ループ (Procedural Loops) の禁止**

理由: 空のリストを作成し、ループ内で append する処理は、コードを行単位で追う必要があり可読性が低いため。  
ルール:

* for 文を使ってリストや辞書を構築することを禁止する。  
* 原則として **リスト内包表記** を使用する。

Python

\# ❌ Bad: 手続き的  
active\_users \= \[\]  
for user in users:  
    if user.is\_active:  
        active\_users.append(user.name)

\# ✅ Good: 宣言的  
active\_users \= \[user.name for user in users if user.is\_active\]

## **3.2 三項演算子の厳格化**

理由: ネストされた条件式は解読が困難であるため。  
ルール:

* ネストされた三項演算子 (A if X else B if Y else C) は禁止。  
* 条件式内で関数呼び出しを含む複雑な計算を行うことを禁止。

## **3.3 可変デフォルト引数の禁止**

理由: Python の仕様上、デフォルト引数は一度だけ評価され共有されるため、重大なバグ（参照の共有）を引き起こす。  
ルール: items: list \= \[\] は禁止。必ず items: list | None \= None とし、内部で初期化する。

## **3.4 Any 型の完全禁止**

理由: 型システムの無効化と同義であるため。  
ルール:

* Any は使用禁止。ジェネリクス (TypeVar) や Protocol、object で代替する。  
* ライブラリの都合等でどうしても型付けできない場合は、type: ignore\[code\] で明示的に警告を抑制する。

# **4\. 変数と型システム (Variables & Type System)**

## **4.1 再代入の回避と Final**

**ルール:**

* 変数の再代入は極力避ける。  
* 定数や重要な変数には typing.Final を付与し、意図しない変更を防ぐ。

## **4.2 Protocol による抽象化**

定義: 抽象基底クラス (abc.ABC) の継承ではなく、typing.Protocol を使用してインターフェースを定義する。  
理由: 実装クラスがインターフェースを意識（継承）する必要がなくなり、疎結合を保てるため（Goのinterfaceに近い運用）。

## **4.3 Optional の明示**

**ルール:** None を許容する場合は、必ず Type | None (Python 3.10+) と明記する。

# **5\. 非同期処理とエラーハンドリング (Async & Error Handling)**

## **5.1 ネイティブ Result パターンの採用**

方針: 予測可能なドメインエラー（バリデーション、データ不在等）には、例外 (raise) ではなく Union型 (Result) を返す。  
実装: ライブラリに依存せず、Python 3.10+ の match 文を活用する。

Python

\# ✅ Good  
def divide(a: int, b: int) \-\> float | Error:  
    if b \== 0:  
        return Error("Division by zero")  
    return a / b

\# 呼び出し側  
match divide(10, 0):  
    case float(val): ...  
    case Error(e): ...

## **5.2 構造化された並行処理**

**ルール:**

* create\_task をそのまま使用して「投げっぱなし」にすることを禁止する。  
* 並列実行が必要な場合は、必ず asyncio.TaskGroup (Python 3.11+) または asyncio.gather を使用し、タスクの寿命と例外を管理下におく。

## **5.3 タイムゾーンの強制**

**ルール:**

* 日付操作は必ず zoneinfo を使用し、Timezone Aware な状態で行う。  
* datetime.now() (引数なし) は禁止。必ず datetime.now(ZoneInfo("UTC")) 等とする。

# **6\. ファイル構造と命名規則 (File Structure & Naming)**

## **6.1 機能単位の構造 (Feature-based Structure)**

技術レイヤー（Controller, Service, Dao）ではなく、ドメイン（機能）ごとにディレクトリを切る「コロケーション（Colocation）」原則を採用する。

Plaintext

src/  
  domain/  
    users/              \# 機能単位  
      schemas.py        \# Data Object  
      services.py       \# Service Object  
      exceptions.py     \# エラー定義  
    orders/  
      ...  
  shared/               \# 共有ユーティリティ

## **6.2 命名規則**

* **ファイル名:** スネークケース (e.g., user\_service.py)  
* **クラス名:** パスカルケース (e.g., UserService)  
* **変数/関数:** スネークケース (e.g., get\_user)  
* **定数:** アッパースネークケース (e.g., MAX\_RETRY)  
* **サフィックス:** クラスの役割を名前に含める (\~Service, \~Repository, \~Schema)。

# **7\. 強制と自動化 (Enforcement)**

本規約は開発者の注意力ではなく、以下のツール設定によって物理的に強制される。

## **7.1 Ruff 設定 (pyproject.toml)**

Ini, TOML

\[tool.ruff.lint\]  
select \= \[  
    "F", "E", "W",   \# Standard  
    "B",             \# flake8-bugbear (可変デフォルト引数等の禁止)  
    "ANN",           \# flake8-annotations (型ヒントの強制)  
    "C4",            \# flake8-comprehensions (リスト内包表記の強制)  
    "SIM",           \# flake8-simplify (構文の単純化)  
    "RET",           \# flake8-return (早期リターンの推奨)  
    "ARG",           \# flake8-unused-arguments  
    "PLR1706",       \# ネストされた三項演算子の禁止  
    "PLR0913",       \# 引数過多の禁止  
    "TID",           \# インポートルールの強制  
\]  
extend-select \= \["ANN401"\] \# Any型の禁止

\[tool.ruff.lint.mccabe\]  
max-complexity \= 10  \# 複雑度の制限

## **7.2 Mypy 設定 (pyproject.toml)**

Ini, TOML

\[tool.mypy\]  
strict \= true                \# 最も厳格なモード  
disallow\_any\_generics \= true \# ジェネリクスの型省略禁止  
warn\_return\_any \= true       \# Anyが返ることを警告  
no\_implicit\_optional \= true  \# 暗黙のNone許容を禁止  
