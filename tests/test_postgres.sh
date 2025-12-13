#!/bin/bash
set -e

# 色の定義
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8080"

echo "=== FastAPI Backend Test Script (PostgreSQL) ==="

# .envファイルを読み込む (存在する場合)
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# DSNの構築 (デフォルト値も設定)
# docker-compose.yamlのサービス名は "postgres"
PG_USER=${POSTGRES_USER:-postgres}
PG_PASS=${POSTGRES_PASSWORD:-postgres}
PG_DB=${POSTGRES_DB:-db}
PG_HOST="postgres"
PG_PORT="5432"

# init_postgres.py に渡すための DSN
# アプリケーションが .env.local 等で設定済みの場合はそれが優先されるかもしれないが、
# ここでは明示的に渡すことで初期化を確実にする。
DSN="postgresql+asyncpg://${PG_USER}:${PG_PASS}@${PG_HOST}:${PG_PORT}/${PG_DB}"

echo "Using DSN for initialization: $DSN"

# 1. PostgreSQLテーブルの初期化
echo -e "\n[1] Initializing PostgreSQL tables..."
# コンテナ内でスクリプトを実行してテーブルを作成
# POSTGRES_DSN 環境変数を渡して実行
if docker compose exec -e POSTGRES_DSN="$DSN" app uv run python scripts/init_postgres.py; then
    echo -e "${GREEN}PostgreSQL tables initialized successfully.${NC}"
else
    echo -e "${RED}Failed to initialize PostgreSQL tables.${NC}"
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
  "path": "/hello-world-postgres",
  "method": "GET",
  "status_code": 200,
  "response_body": {"message": "Hello from Postgres Mock!"},
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
MOCK_RESPONSE=$(curl -s "${BASE_URL}/hello-world-postgres")
echo "Mock Response: $MOCK_RESPONSE"

if [[ $MOCK_RESPONSE == *"Hello from Postgres Mock!"* ]]; then
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

echo -e "\n${GREEN}=== All Tests Passed (PostgreSQL) ===${NC}"
