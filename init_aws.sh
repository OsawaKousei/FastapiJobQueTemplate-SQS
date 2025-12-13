#!/bin/bash
set -e # エラー発生時にスクリプトを停止

REGION="ap-northeast-1"
QUEUE_NAME="job-queue"
TABLE_NAME="Jobs"
PROXY_FUNC_NAME="worker-proxy"

echo "=== AWS Resource Setup Start ==="

# ------------------------------------------------------------
# 1. DynamoDB テーブル作成 (Streams有効化)
# ------------------------------------------------------------
echo "Creating DynamoDB table: $TABLE_NAME"
awslocal dynamodb create-table \
    --table-name $TABLE_NAME \
    --attribute-definitions AttributeName=job_id,AttributeType=S \
    --key-schema AttributeName=job_id,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region $REGION \
    --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES

# ------------------------------------------------------------
# 2. SQS キュー作成
# ------------------------------------------------------------
echo "Creating SQS queue: $QUEUE_NAME"
awslocal sqs create-queue --queue-name $QUEUE_NAME --region $REGION

# ------------------------------------------------------------
# 3. Proxy Lambda 作成 (LWAの挙動を模倣)
# ------------------------------------------------------------
echo "Creating Proxy Lambda function..."

# 転送用Pythonスクリプトの作成
cat <<EOF > proxy.py
import urllib.request
import json
import os

def handler(event, context):
    # 環境変数からWorkerのURLを取得 (デフォルトは http://worker:8080)
    url = os.environ.get("WORKER_ENDPOINT", "http://worker:8080")
    print(f"Forwarding event to: {url}")

    # リクエストの作成
    # SQSのイベント(dict)をそのままJSONにしてPOSTする
    data = json.dumps(event).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'LocalStack-Proxy-Lambda'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as res:
            response_body = res.read().decode('utf-8')
            print(f"Worker response status: {res.getcode()}")
            
            # Workerが2xx以外を返した場合、例外を投げてSQSにリトライさせる
            if not (200 <= res.getcode() < 300):
                raise Exception(f"Worker returned error: {res.getcode()} {response_body}")
                
            return {"statusCode": res.getcode(), "body": "Forwarded successfully"}
            
    except Exception as e:
        print(f"Error forwarding to worker: {e}")
        # ここで例外を投げると、SQSメッセージは処理失敗とみなされ、リトライキューに戻る
        raise e
EOF

# Zip化
zip proxy.zip proxy.py

# Lambda関数の登録
awslocal lambda create-function \
    --function-name $PROXY_FUNC_NAME \
    --runtime python3.12 \
    --handler proxy.handler \
    --role arn:aws:iam::000000000000:role/lambda-role \
    --zip-file fileb://proxy.zip \
    --region $REGION \
    --timeout 30 \
    --environment Variables="{WORKER_ENDPOINT=http://worker:8080}"

# ------------------------------------------------------------
# 4. イベントソースマッピング (SQS -> Lambda)
# ------------------------------------------------------------
echo "Mapping SQS to Lambda..."

QUEUE_ARN=$(awslocal sqs get-queue-attributes \
    --queue-url http://localhost:4566/000000000000/$QUEUE_NAME \
    --attribute-name QueueArn \
    --query Attributes.QueueArn \
    --output text)

awslocal lambda create-event-source-mapping \
    --function-name $PROXY_FUNC_NAME \
    --event-source-arn $QUEUE_ARN \
    --batch-size 1 \
    --region $REGION

# ------------------------------------------------------------
# クリーンアップ
# ------------------------------------------------------------
rm proxy.py proxy.zip

echo "=== AWS Resource Setup Complete ==="