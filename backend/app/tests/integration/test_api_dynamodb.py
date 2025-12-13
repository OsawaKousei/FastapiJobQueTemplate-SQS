import boto3
import pytest
from fastapi.testclient import TestClient

from src.config import get_settings
from src.main import app


@pytest.fixture(scope="function", autouse=True)
def force_dynamodb(monkeypatch):
    """Ensure the app uses DynamoDB during these tests."""
    monkeypatch.setenv("DB_TYPE", "dynamodb")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(scope="function")
def dynamodb_resource():
    settings = get_settings()
    return boto3.resource(
        "dynamodb",
        endpoint_url=settings.dynamodb_endpoint_url,
        region_name=settings.aws_default_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


@pytest.fixture(scope="function", autouse=True)
def setup_table(dynamodb_resource):
    table_name = "MockTable"
    try:
        table = dynamodb_resource.Table(table_name)
        table.load()
        table.delete()
        table.wait_until_not_exists(WaiterConfig={"Delay": 1, "MaxAttempts": 5})
    except dynamodb_resource.meta.client.exceptions.ResourceNotFoundException:
        pass

    table = dynamodb_resource.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "method", "KeyType": "HASH"},
            {"AttributeName": "path", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "method", "AttributeType": "S"},
            {"AttributeName": "path", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists(WaiterConfig={"Delay": 1, "MaxAttempts": 10})
    yield
    table.delete()
    table.wait_until_not_exists(WaiterConfig={"Delay": 1, "MaxAttempts": 5})


@pytest.fixture
def client():
    return TestClient(app)


def test_e2e_mock_lifecycle(client):
    # 1. Create Mock
    mock_data = {
        "path": "/test/api",
        "method": "GET",
        "status_code": 200,
        "response_body": {"message": "Hello World"},
        "headers": {"X-Custom": "Test"},
        "latency_ms": 0,
    }
    response = client.post("/api/mocks", json=mock_data)
    assert response.status_code == 201
    created_mock = response.json()
    mock_id = created_mock["id"]
    assert created_mock["path"] == "/test/api"

    # 2. Simulate Mock
    response = client.get("/test/api")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
    assert response.headers["X-Custom"] == "Test"

    # 3. Delete Mock
    response = client.delete(f"/api/mocks/{mock_id}")
    assert response.status_code == 204

    # 4. Verify Deletion (Simulation should fail)
    response = client.get("/test/api")
    assert response.status_code == 404


def test_template_rendering(client):
    # 1. Create Mock with Template
    mock_data = {
        "path": "/test/template",
        "method": "GET",
        "status_code": 200,
        "response_body": {"id": "{{uuid}}", "timestamp": "{{now_iso}}"},
        "headers": {},
        "latency_ms": 0,
    }
    response = client.post("/api/mocks", json=mock_data)
    assert response.status_code == 201

    # 2. Simulate Mock
    response = client.get("/test/template")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert len(data["id"]) == 36  # UUID length
    assert "timestamp" in data
