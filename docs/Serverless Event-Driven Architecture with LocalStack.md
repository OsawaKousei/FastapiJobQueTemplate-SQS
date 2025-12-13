# **Serverless Event-Driven Architecture with LocalStack**

## **1\. アーキテクチャ概要**

FastAPIをフロントエンドとし、重い処理を非同期のLambdaワーカーに委譲するサーバーレスアーキテクチャです。LocalStackの高度な機能（Docker in Docker, Event Source Mapping）を活用し、ポーリングコードを一切書かずにイベント駆動を実現します。

### **システム構成図**

コード スニペット

sequenceDiagram  
    participant Client  
    participant API as FastAPI (Container)  
    participant DDB as DynamoDB (LocalStack)  
    participant SQS as SQS (LocalStack)  
    participant Lambda as Lambda Worker (Container)

    Client-\>\>API: POST /jobs (Payload)  
    API-\>\>DDB: Put Item (Status: QUEUED)  
    API-\>\>SQS: Send Message (Job ID)  
    API--\>\>Client: Return Job ID

    Note over SQS,Lambda: Event Source Mapping (Auto Trigger)  
    SQS-\>\>Lambda: Invoke Handler (Event)  
      
    activate Lambda  
    Lambda-\>\>DDB: Update Item (Status: PROCESSING)  
    Lambda-\>\>Lambda: Heavy Computation...  
    Lambda-\>\>DDB: Update Item (Status: COMPLETED)  
    deactivate Lambda

    Client-\>\>API: GET /jobs/{id}  
    API-\>\>DDB: Get Item  
    DDB--\>\>API: Return Status & Result  
    API--\>\>Client: JSON Response

## ---

**2\. ディレクトリ構成**

ホストマシンの app/ ディレクトリを、APIサーバーとLambdaコンテナの両方にマウントすることで、コードの共有とホットリロードを実現します。

Plaintext

.  
├── docker-compose.yml      \# インフラ定義  
├── init\_aws.sh             \# AWSリソース初期化スクリプト  
└── app/                    \# アプリケーションコード (API & Worker共有)  
    ├── main.py             \# FastAPI エントリーポイント  
    ├── worker.py           \# Lambda ハンドラー  
    ├── logic.py            \# 共通ビジネスロジック (DB操作など)  
    └── requirements.txt    \# 依存ライブラリ

## ---

**3\. 設定ファイル詳細**

### **docker-compose.yml**

この構成の核となるファイルです。LAMBDA\_DOCKER\_FLAGS により、LocalStackが起動する一時的なLambdaコンテナに対して、ホストのディレクトリをマウントさせます。

YAML

version: '3.8'

services:  
  \# \--- 1\. API Server (FastAPI) \---  
  api:  
    image: python:3.9-slim  
    container\_name: fastapi\_server  
    volumes:  
      \- ./app:/app  \# ホットリロード用にマウント  
    working\_dir: /app  
    \# 依存ライブラリを入れてサーバー起動  
    command: \>  
      sh \-c "pip install \-r requirements.txt &&   
             uvicorn main:app \--host 0.0.0.0 \--port 8080 \--reload"  
    ports:  
      \- "8080:8080"  
    environment:  
      \- AWS\_ENDPOINT\_URL=http://localstack:4566  
      \- AWS\_DEFAULT\_REGION=ap-northeast-1  
    depends\_on:  
      \- localstack  
    networks:  
      \- app-network

  \# \--- 2\. AWS Mock (LocalStack) \---  
  localstack:  
    image: localstack/localstack:latest  
    container\_name: localstack\_main  
    ports:  
      \- "4566:4566"  
    environment:  
      \- SERVICES=sqs,dynamodb,lambda  
      \- DEBUG=1  
      \- AWS\_DEFAULT\_REGION=ap-northeast-1  
      \- DOCKER\_HOST=unix:///var/run/docker.sock  
      \# ★重要: Lambda起動時にホストの ./app を /var/task/app にマウントする  
      \# これにより、zipデプロイ不要でコード変更が即反映される  
      \- LAMBDA\_DOCKER\_FLAGS=-v ${PWD}/app:/var/task/app  
    volumes:  
      \# Docker in Docker (Lambdaコンテナ起動用)  
      \- "/var/run/docker.sock:/var/run/docker.sock"  
      \# 初期化スクリプト  
      \- "./init\_aws.sh:/etc/localstack/init/ready.d/init\_aws.sh"  
    networks:  
      \- app-network

networks:  
  app-network:  
    driver: bridge

### **init\_aws.sh (初期化スクリプト)**

コンテナ起動時に実行され、DynamoDBテーブル、SQS、Lambda関数を作成し、イベントマッピング（トリガー）を設定します。

Bash

\#\!/bin/bash  
REGION="ap-northeast-1"  
QUEUE\_NAME="job-queue"  
TABLE\_NAME="Jobs"  
FUNC\_NAME="worker"

echo "=== AWS Resource Setup Start \==="

\# 1\. DynamoDB テーブル作成  
awslocal dynamodb create-table \\  
    \--table-name $TABLE\_NAME \\  
    \--attribute-definitions AttributeName=job\_id,AttributeType=S \\  
    \--key-schema AttributeName=job\_id,KeyType=HASH \\  
    \--provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \\  
    \--region $REGION

\# 2\. SQS キュー作成  
awslocal sqs create-queue \--queue-name $QUEUE\_NAME \--region $REGION

\# 3\. Lambda 関数作成  
\# ダミーのzipを作成 (実際の中身はDockerマウントで上書きされるため何でも良い)  
echo "def handler(e,c): pass" \> dummy.py  
zip dummy.zip dummy.py

\# 関数登録  
\# handlerに "app.worker.handler" を指定することで、  
\# マウントされた /var/task/app/worker.py を参照させる  
awslocal lambda create-function \\  
    \--function-name $FUNC\_NAME \\  
    \--runtime python3.9 \\  
    \--handler app.worker.handler \\  
    \--role arn:aws:iam::000000000000:role/lambda-role \\  
    \--zip-file fileb://dummy.zip \\  
    \--region $REGION \\  
    \--timeout 30 \\  
    \--environment Variables="{AWS\_ENDPOINT\_URL=http://localstack:4566, TABLE\_NAME=$TABLE\_NAME}"

\# 4\. イベントソースマッピング (SQS \-\> Lambda)  
QUEUE\_ARN=$(awslocal sqs get-queue-attributes \--queue-url http://localhost:4566/000000000000/$QUEUE\_NAME \--attribute-name QueueArn \--query Attributes.QueueArn \--output text)

awslocal lambda create-event-source-mapping \\  
    \--function-name $FUNC\_NAME \\  
    \--event-source-arn $QUEUE\_ARN \\  
    \--batch-size 1 \\  
    \--region $REGION

echo "=== AWS Resource Setup Complete \==="

## ---

**4\. アプリケーションコード**

app/ フォルダ配下に配置します。

### **app/requirements.txt**

Plaintext

fastapi  
uvicorn  
boto3  
pydantic

### **app/logic.py (共通ロジック)**

APIとワーカーの両方で使うデータベース操作やビジネスロジックを集約します。

Python

import boto3  
import os  
import time

\# コンテナ内からLocalStackへの接続設定  
ENDPOINT \= os.getenv("AWS\_ENDPOINT\_URL", "http://localstack:4566")  
REGION \= "ap-northeast-1"  
TABLE\_NAME \= os.getenv("TABLE\_NAME", "Jobs")

\# リソースの初期化 (モジュールロード時に1回だけ実行)  
dynamodb \= boto3.resource("dynamodb", endpoint\_url=ENDPOINT, region\_name=REGION)  
table \= dynamodb.Table(TABLE\_NAME)

def process\_job\_logic(job\_id: str):  
    """  
    ジョブの実行ロジック。Lambdaから呼び出される。  
    """  
    print(f"\[Logic\] Start processing job: {job\_id}")

    \# 1\. ステータスを処理中に更新  
    table.update\_item(  
        Key={'job\_id': job\_id},  
        UpdateExpression="set \#st \= :s",  
        ExpressionAttributeNames={'\#st': 'status'},  
        ExpressionAttributeValues={':s': 'PROCESSING'}  
    )

    \# \--- ここに重い処理を記述 \---  
    time.sleep(3) \# 処理のシミュレーション  
    result\_data \= "Success via LocalStack"  
    \# \------------------------

    \# 2\. ステータスを完了に更新  
    table.update\_item(  
        Key={'job\_id': job\_id},  
        UpdateExpression="set \#st \= :s, \#r \= :r",  
        ExpressionAttributeNames={'\#st': 'status', '\#r': 'result'},  
        ExpressionAttributeValues={':s': 'COMPLETED', ':r': result\_data}  
    )  
    print(f"\[Logic\] Job {job\_id} completed.")

### **app/worker.py (Lambda エントリーポイント)**

Lambdaのお作法（ハンドラー関数）に従い、共通ロジックを呼び出します。

Python

from app.logic import process\_job\_logic

def handler(event, context):  
    """  
    SQSトリガーによってLocalStackから呼び出される関数  
    """  
    print("--- Lambda Worker Triggered \---")  
      
    for record in event\['Records'\]:  
        \# SQSメッセージからJob IDを取得  
        job\_id \= record\['body'\]  
          
        \# 共通ロジックを実行  
        try:  
            process\_job\_logic(job\_id)  
        except Exception as e:  
            print(f"Error processing {job\_id}: {e}")  
            raise e \# 例外を投げるとSQSのリトライ機能が働く  
              
    return {"status": "success"}

### **app/main.py (FastAPI サーバー)**

リクエストを受け付け、DynamoDBへの初期登録とSQSへのメッセージ送信を行います。

Python

from fastapi import FastAPI  
from pydantic import BaseModel  
import boto3  
import uuid  
import os  
from app.logic import table \# 共通ロジックからテーブル定義を再利用

app \= FastAPI()

\# SQSクライアントの準備  
ENDPOINT \= os.getenv("AWS\_ENDPOINT\_URL", "http://localstack:4566")  
sqs \= boto3.client("sqs", endpoint\_url=ENDPOINT, region\_name="ap-northeast-1")  
QUEUE\_NAME \= "job-queue"

class JobRequest(BaseModel):  
    payload: str

@app.post("/jobs")  
def create\_job(req: JobRequest):  
    job\_id \= str(uuid.uuid4())  
      
    \# 1\. DynamoDBへ初期ステータス登録  
    table.put\_item(Item={  
        "job\_id": job\_id,  
        "status": "QUEUED",  
        "payload": req.payload  
    })  
      
    \# 2\. SQSへJob IDを送信  
    \# (毎回URLを取得するのは非効率だが、LocalStack起動待ち対策として安全)  
    q\_url \= sqs.get\_queue\_url(QueueName=QUEUE\_NAME)\["QueueUrl"\]  
    sqs.send\_message(QueueUrl=q\_url, MessageBody=job\_id)  
      
    return {"job\_id": job\_id, "status": "QUEUED"}

@app.get("/jobs/{job\_id}")  
def get\_job\_status(job\_id: str):  
    response \= table.get\_item(Key={"job\_id": job\_id})  
    if "Item" not in response:  
        return {"error": "Job not found"}  
    return response\["Item"\]

## ---

**5\. 実行と確認手順**

### **ステップ 1: 起動**

Bash

docker compose up

ログに \=== AWS Resource Setup Complete \=== が表示されるまで待ちます。

### **ステップ 2: ジョブの投入 (FastAPI)**

別のターミナルからリクエストを送ります。

Bash

curl \-X POST "http://localhost:8080/jobs" \\  
     \-H "Content-Type: application/json" \\  
     \-d '{"payload": "test-data"}'

レスポンス:  
{"job\_id":"\<UUID\>", "status":"QUEUED"}

### **ステップ 3: 処理の確認 (LocalStack Logs)**

Dockerのログを見ると、APIのリクエスト直後にLambdaが起動していることがわかります。

Plaintext

api\_1        | POST /jobs HTTP/1.1 200 OK  
localstack\_1 | \> \--- Lambda Worker Triggered \---  
localstack\_1 | \> \[Logic\] Start processing job: \<UUID\>  
localstack\_1 | \> \[Logic\] Job \<UUID\> completed.

### **ステップ 4: 結果の取得 (FastAPI)**

Bash

curl "http://localhost:8080/jobs/\<UUID\>"

レスポンス:  
{"job\_id":"\<UUID\>", "status":"COMPLETED", "result":"Success via LocalStack", ...}

## ---

**6\. 本番環境 (AWS) への適用**

この構成は、本番環境への移行が非常にスムーズです。

| コンポーネント | ローカル (LocalStack) | 本番 (AWS Cloud) |
| :---- | :---- | :---- |
| **API** | Docker Container (FastAPI) | AWS App Runner / ECS / EKS |
| **Worker** | Docker Container (Lambdaマウント) | **AWS Lambda (Container Image)** |
| **コード** | ホストボリュームマウント | Docker Image (COPY . /app) |

本番デプロイ時のポイント:  
本番用 Dockerfile では、COPY ./app /var/task/app を記述し、CMDを app.worker.handler に設定するだけで、そのままLambda用のコンテナイメージとして動作します。コードの変更は一切不要です。