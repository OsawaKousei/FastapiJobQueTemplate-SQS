#!/bin/bash
set -e

# 色の定義
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8080"

echo "=== FastAPI Backend Test Script ==="

# 1. DynamoDBテーブルの初期化
echo -e "\n[1] Initializing DynamoDB table..."
# コンテナ内でスクリプトを実行してテーブルを作成
if docker compose exec app uv run python scripts/init_dynamodb.py; then
    echo -e "${GREEN}DynamoDB table initialized successfully.${NC}"
else
    echo -e "${RED}Failed to initialize DynamoDB table.${NC}"
    exit 1
fi

# 2. ヘルスチェック
echo -e "\n[2] Checking Health Endpoint..."
HEALTH_RESPONSE=$(curl -s "${BASE_URL}/")
echo "Response: $HEALTH_RESPONSE"

if [[ $HEALTH_RESPONSE == *"ok"* ]]; then
    echo -e "${GREEN}Health check passed.${NC}"
else
    echo -e "${RED}Health check failed.${NC}"
    exit 1
fi

# 3. モックの作成
echo -e "\n[3] Creating a Mock Endpoint..."
MOCK_PAYLOAD='{
  "path": "/hello-world",
  "method": "GET",
  "status_code": 200,
  "response_body": {"message": "Hello from Mock!"},
  "headers": {"Content-Type": "application/json"},
  "latency_ms": 0
}'

CREATE_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/mocks" \
  -H "Content-Type: application/json" \
  -d "$MOCK_PAYLOAD")

echo "Create Response: $CREATE_RESPONSE"

# IDの抽出 (jqがない場合も考慮してgrep/sedで簡易抽出)
MOCK_ID=$(echo $CREATE_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$MOCK_ID" ]; then
    echo -e "${GREEN}Mock created with ID: $MOCK_ID${NC}"
else
    echo -e "${RED}Failed to create mock.${NC}"
    exit 1
fi

# 4. モックの動作確認
echo -e "\n[4] Testing the Mock Endpoint..."
MOCK_RESPONSE=$(curl -s "${BASE_URL}/hello-world")
echo "Mock Response: $MOCK_RESPONSE"

if [[ $MOCK_RESPONSE == *"Hello from Mock!"* ]]; then
    echo -e "${GREEN}Mock test passed.${NC}"
else
    echo -e "${RED}Mock test failed.${NC}"
    exit 1
fi

# 5. モックの削除
echo -e "\n[5] Deleting the Mock Endpoint..."
DELETE_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${BASE_URL}/api/mocks/${MOCK_ID}")

if [ "$DELETE_CODE" -eq 204 ]; then
    echo -e "${GREEN}Mock deleted successfully.${NC}"
else
    echo -e "${RED}Failed to delete mock. Status code: $DELETE_CODE${NC}"
    exit 1
fi

echo -e "\n${GREEN}=== All Tests Passed ===${NC}"
