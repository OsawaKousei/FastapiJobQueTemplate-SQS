#!/bin/bash

# エラーハンドリング: エラーが発生したら停止
set -e

BASE_URL="http://localhost:8080"

echo "=== Job Queue System Test Start ==="

# 1. ジョブの投入
echo "[1] Submitting a job..."
PAYLOAD='{"payload": "test-task"}'
echo "Request Payload: $PAYLOAD"

RESPONSE=$(curl -s -X POST "$BASE_URL/jobs"      -H "Content-Type: application/json"      -d "$PAYLOAD")

echo "Response: $RESPONSE"

# job_id を抽出
JOB_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('job_id', ''))")

if [ -z "$JOB_ID" ]; then
    echo "Error: Failed to extract job_id."
    exit 1
fi

echo "Extracted Job ID: $JOB_ID"
echo "-----------------------------------"

# 2. ステータスのポーリング確認 (最大30秒待機)
echo "[2] Polling job status..."

MAX_RETRIES=15
SLEEP_SECONDS=2

for ((i=1; i<=MAX_RETRIES; i++)); do
    STATUS_RESPONSE=$(curl -s "$BASE_URL/jobs/$JOB_ID")
    STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', ''))")
    
    echo "Attempt $i: Status is $STATUS"

    if [ "$STATUS" == "COMPLETED" ]; then
        echo "Job completed successfully!"
        echo "Final Response: $STATUS_RESPONSE"
        echo "=== Test Finished (Success) ==="
        exit 0
    elif [ "$STATUS" == "FAILED" ]; then
        echo "Job failed."
        echo "Final Response: $STATUS_RESPONSE"
        echo "=== Test Finished (Failed) ==="
        exit 1
    fi

    sleep $SLEEP_SECONDS
done

echo "Timeout: Job did not complete within $((MAX_RETRIES * SLEEP_SECONDS)) seconds."
echo "Current Status: $STATUS"
exit 1
