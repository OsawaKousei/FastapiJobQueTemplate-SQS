#!/bin/bash
set -e

# 色の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# エンドポイントURLを引数から取得
API_ENDPOINT="$1"

# エンドポイントが指定されていない場合はエラー
if [ -z "$API_ENDPOINT" ]; then
    echo -e "${RED}Usage: $0 <API_ENDPOINT>${NC}"
    echo -e "Example: $0 https://abc123.lambda-url.ap-northeast-1.on.aws"
    exit 1
fi

# 末尾のスラッシュを削除
API_ENDPOINT="${API_ENDPOINT%/}"

echo "=== AWS Deployed API Test Script ==="
echo -e "Endpoint: ${YELLOW}${API_ENDPOINT}${NC}"
echo ""

# 1. ヘルスチェック
echo -e "[1] Health Check..."
HEALTH_RESPONSE=$(curl -s "${API_ENDPOINT}/")
echo "Response: $HEALTH_RESPONSE"

if [[ $HEALTH_RESPONSE == *"ok"* ]] || [[ $HEALTH_RESPONSE == *"status"* ]]; then
    echo -e "${GREEN}✓ Health check passed.${NC}"
else
    echo -e "${RED}✗ Health check failed.${NC}"
    echo -e "${YELLOW}Note: The endpoint might need a few minutes to warm up after deployment.${NC}"
fi

# 2. モックの作成
echo -e "\n[2] Creating a Mock Endpoint..."
MOCK_PAYLOAD='{
  "path": "/hello-world",
  "method": "GET",
  "status_code": 200,
  "response_body": {"message": "Hello from AWS Lambda!"},
  "headers": {"Content-Type": "application/json"},
  "latency_ms": 0
}'

CREATE_RESPONSE=$(curl -s -X POST "${API_ENDPOINT}/api/mocks" \
  -H "Content-Type: application/json" \
  -d "$MOCK_PAYLOAD")

echo "Response: $CREATE_RESPONSE"

# IDの抽出
MOCK_ID=$(echo $CREATE_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$MOCK_ID" ]; then
    echo -e "${GREEN}✓ Mock created with ID: ${MOCK_ID}${NC}"
else
    echo -e "${RED}✗ Failed to create mock.${NC}"
    echo "Response was: $CREATE_RESPONSE"
    exit 1
fi

# 4. モックの動作確認
echo -e "\n[4] Testing the Mock Endpoint..."
MOCK_RESPONSE=$(curl -s "${API_ENDPOINT}/hello-world")
echo "Response: $MOCK_RESPONSE"

if [[ $MOCK_RESPONSE == *"Hello from AWS Lambda!"* ]]; then
    echo -e "${GREEN}✓ Mock endpoint works correctly.${NC}"
else
    echo -e "${RED}✗ Mock endpoint test failed.${NC}"
fi

# 6. モックの削除
echo -e "\n[6] Deleting the Mock Endpoint..."
DELETE_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${API_ENDPOINT}/api/mocks/${MOCK_ID}")

if [ "$DELETE_CODE" -eq 204 ] || [ "$DELETE_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Mock deleted successfully (HTTP ${DELETE_CODE}).${NC}"
else
    echo -e "${RED}✗ Failed to delete mock. Status code: ${DELETE_CODE}${NC}"
fi

# 7. 削除確認
echo -e "\n[7] Verifying deletion..."
VERIFY_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${API_ENDPOINT}/hello-world")

if [ "$VERIFY_RESPONSE" -eq 404 ]; then
    echo -e "${GREEN}✓ Mock endpoint no longer exists (HTTP 404).${NC}"
else
    echo -e "${YELLOW}! Unexpected status: ${VERIFY_RESPONSE}${NC}"
fi

echo -e "\n${GREEN}=== All Tests Completed ===${NC}"
echo -e "\nAPI Endpoint: ${YELLOW}${API_ENDPOINT}${NC}"
echo -e "Region: ${YELLOW}${REGION}${NC}"
echo -e "Profile: ${YELLOW}${AWS_PROFILE}${NC}"
API Endpoint: ${YELLOW}${API_ENDPOINT