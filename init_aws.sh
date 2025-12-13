#!/bin/bash
REGION="ap-northeast-1"
QUEUE_NAME="job-queue"
TABLE_NAME="Jobs"
FUNC_NAME="worker"

echo "=== AWS Resource Setup Start ==="

# 1. DynamoDB テーブル作成
awslocal dynamodb create-table \
    --table-name $TABLE_NAME \
    --attribute-definitions AttributeName=job_id,AttributeType=S \
    --key-schema AttributeName=job_id,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region $REGION

# 2. SQS キュー作成
awslocal sqs create-queue --queue-name $QUEUE_NAME --region $REGION

# 3. Lambda 関数作成
# ダミーのzipを作成 (実際の中身はDockerマウントで上書きされるため何でも良い)
echo "def handler(e,c): pass" > dummy.py
zip dummy.zip dummy.py

# 関数登録
# handlerに "app.src.worker.handler" を指定することで、
# マウントされた /var/task/app/src/worker.py を参照させる
# 注意: LocalStackのマウントパスは docker-compose.yml で設定する
# ここでは /var/task/app がホストの ./app に対応すると仮定
awslocal lambda create-function \
    --function-name $FUNC_NAME \
    --runtime python3.12 \
    --handler app.src.worker.handler \
    --role arn:aws:iam::000000000000:role/lambda-role \
    --zip-file fileb://dummy.zip \
    --region $REGION \
    --timeout 30 \
    --environment Variables="{AWS_ENDPOINT_URL=http://localstack:4566, TABLE_NAME=$TABLE_NAME}"

# 4. イベントソースマッピング (SQS -> Lambda)
QUEUE_ARN=$(awslocal sqs get-queue-attributes --queue-url http://localhost:4566/000000000000/$QUEUE_NAME --attribute-name QueueArn --query Attributes.QueueArn --output text)

awslocal lambda create-event-source-mapping \
    --function-name $FUNC_NAME \
    --event-source-arn $QUEUE_ARN \
    --batch-size 1 \
    --region $REGION

echo "=== AWS Resource Setup Complete ==="
