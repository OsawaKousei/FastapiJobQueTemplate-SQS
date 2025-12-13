#!/bin/bash

# エラーハンドリング: エラーが発生したら停止
set -e

BASE_URL="http://localhost:8080"

echo "=== Job Queue System Test Start ==="

# 1. ジョブの投入
echo "[1] Submitting a job..."
PAYLOAD='{"payload": "test-task"}'
echo "Request Payload: $PAYLOAD"

RESPONSE=$(curl -s -X POST "$BASE_URL/jobs" \
     -H "Content-Type: application/json" \
     -d "$PAYLOAD")

echo "Response: $RESPONSE"

# job_id を抽出 (Pythonを使用してJSONパース)
JOB_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('job_id', ''))")

if [ -z "$JOB_ID" ]; then
    echo "Error: Failed to extract job_id."
    exit 1
fi

echo "Extracted Job ID: $JOB_ID"
echo "-----------------------------------"

# 2. ステータスの確認
echo "[2] Checking job status..."
echo "Requesting: $BASE_URL/jobs/$JOB_ID"

STATUS_RESPONSE=$(curl -s "$BASE_URL/jobs/$JOB_ID")
echo "Status Response: $STATUS_RESPONSE"

echo "=== Test Finished ==="
