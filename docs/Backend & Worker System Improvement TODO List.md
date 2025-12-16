# **Backend & Worker System Improvement TODO List**

## **1\. Infrastructure (Terraform / AWS Configuration)**

このセクションは terraform/ または docker-compose.yaml (LocalStack) の設定変更を含みます。

* \[ \] **A. DLQ (Dead Letter Queue) の作成と紐付け**  
  * \[ \] 新規SQSキュー（例: jobs-dlq）を作成する。  
  * \[ \] メインキューの redrive\_policy に以下を設定する。  
    * deadLetterTargetArn: 作成したDLQのARN  
    * maxReceiveCount: 3〜5程度（何回失敗したらDLQ送りにするか）  
* \[ \] **1\. Batch Size の最適化と部分失敗の有効化**  
  * \[ \] Lambda Event Source Mapping の batch\_size を 1 から 10（またはそれ以上）に変更する。  
  * \[ \] **重要:** function\_response\_types に \["ReportBatchItemFailures"\] を設定する。（これによりLambdaが失敗したメッセージIDだけをSQSに返却可能になる）  
* \[ \] **B. Timeout 設定の整合性確保**  
  * \[ \] Worker Lambdaの timeout を設定する（例: 60秒）。  
  * \[ \] SQSの visibility\_timeout\_seconds を **「Lambda Timeout × 6」** または **「Lambda Timeout \+ バッファ（最低10秒）」** に設定する。  
* \[ \] **2\. DynamoDB TTL (Time To Live) の有効化**  
  * \[ \] DynamoDBテーブル設定で TTL を有効化する。  
  * \[ \] 対象属性名（Attribute Name）を expires\_at に設定する。

## **2\. Common Core (Shared Logic & Interfaces)**

common/ ディレクトリ内の共通ロジックの改修です。  
※ジョブ定義（Schema）については別ドキュメント参照。

* \[ \] **Repositoryへのロック機構の実装 (冪等性)**  
  * \[ \] JobRepository クラスに lock\_job(job\_id: str) \-\> bool メソッドを追加する。  
  * \[ \] UpdateItem を使用し、ConditionExpression で status \= "QUEUED" の場合のみ更新するロジックを実装する。  
  * \[ \] ロック取得失敗時（ConditionalCheckFailedException）は False を返すようにする。  
* \[ \] **TTL設定ロジックの追加**  
  * \[ \] ジョブ作成時（create\_job）または完了時（complete\_job）に、expires\_at（現在のUnix Timestamp \+ 保持期間）を保存するように JobRepository を修正する。  
* \[ \] **Service Interface の抽象化**  
  * \[ \] common/core/interfaces.py を作成し、IWorkerService プロトコルを定義する。  
  * \[ \] メソッドシグネチャを execute(self, payload: Any) \-\> Result とする（Pattern B適用のため）。

## **3\. Worker Implementation (Application Logic)**

worker/ ディレクトリ内の実装変更です。

* \[ \] **Dispatcher の「Pattern B」対応**  
  * \[ \] JobDispatcher クラスを修正し、Serviceインスタンスと共に **Pydantic Model (Schema)** を登録できるようにする。  
  * \[ \] dispatch メソッド内で、受け取った dict を登録された Schema でバリデーション（model\_validate）してから Service に渡すロジックに変更する。  
* \[ \] **Worker Service の実装 (旧 Processor)**  
  * \[ \] processor.py を service.py にリネームし、クラス名を XXWorkerService に変更する。  
  * \[ \] コンストラクタ (\_\_init\_\_) で外部依存（Client, Repositoryなど）を受け取る DI構成にする。  
  * \[ \] execute メソッドの引数を、dict ではなく **具体的なSchema型**（例: EmailJobPayload）に変更する。  
  * \[ \] **冪等性チェック:** execute の冒頭で repo.lock\_job(job\_id) を呼び出し、失敗したら即座に Success(None) (スキップ) を返すようにする。  
* \[ \] **Main Handler の非同期バッチ処理化**  
  * \[ \] main.py (または router.py) のSQSハンドラーを修正する。  
  * \[ \] ループ処理ではなく asyncio.gather を使用して、バッチ内のメッセージを並列処理する。  
  * \[ \] **部分失敗レスポンス:**  
    * 処理成功時は None を返す。  
    * 処理失敗時は messageId を返す。  
    * 最終的な戻り値を {"batchItemFailures": \[{"itemIdentifier": "..."}\]} の形式に整形する。

## **4\. API Implementation (Backend)**

src/ ディレクトリ内の修正です。

* \[ \] **TTLデータの初期投入 (Optional)**  
  * \[ \] 必要であれば、ジョブ登録時 (POST /jobs) に初期の expires\_at を設定するように JobService を調整する。（完了時に更新する方針であれば不要）

### ---

**実装順序の推奨**

1. **Infrastructure**: TerraformでSQS/DynamoDB設定を変更し、デプロイ（またはLocalStack再起動）。  
2. **Common**: Repositoryにロック処理とTTLロジックを追加。  
3. **Worker Core**: DispatcherとMain Handlerを改修し、バッチ処理と型変換の基盤を作る。  
4. **Worker Domain**: 各ドメインのProcessorをService化し、ロック処理を組み込む。