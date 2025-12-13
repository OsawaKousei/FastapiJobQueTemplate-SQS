import uuid

import boto3
import pytest

from src.config import get_settings
from src.domain.mocks.schemas import HttpMethod, MockEndpoint
from src.infrastructure.dynamodb.mock_repository import DynamoMockRepository


@pytest.fixture(scope="module")
def dynamodb_resource():
    settings = get_settings()
    return boto3.resource(
        "dynamodb",
        endpoint_url=settings.dynamodb_endpoint_url,
        region_name=settings.aws_default_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


@pytest.fixture(scope="module")
def setup_table(dynamodb_resource):
    print("Setting up table...")
    table_name = "MockTable"
    try:
        # Check if table exists
        print("Checking if table exists...")
        table = dynamodb_resource.Table(table_name)
        table.load()
        # If exists, delete it to start fresh or just use it?
        # Better to delete and recreate to ensure clean state
        print("Table exists, deleting...")
        table.delete()
        table.wait_until_not_exists(WaiterConfig={"Delay": 1, "MaxAttempts": 5})
        print("Table deleted.")
    except dynamodb_resource.meta.client.exceptions.ResourceNotFoundException:
        print("Table does not exist.")
        pass

    print("Creating table...")
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
    yield table

    # Cleanup
    table.delete()
    table.wait_until_not_exists(WaiterConfig={"Delay": 1, "MaxAttempts": 5})


@pytest.mark.asyncio
async def test_repository_crud(setup_table):
    repo = DynamoMockRepository(table_name="MockTable")

    mock_id = str(uuid.uuid4())
    mock = MockEndpoint(
        id=mock_id,
        path="/test",
        method=HttpMethod.GET,
        status_code=200,
        response_body={"message": "hello"},
        headers={"Content-Type": "application/json"},
        latency_ms=100,
    )

    # Save
    await repo.save(mock)

    # Find
    found = await repo.find(HttpMethod.GET, "/test")
    assert found is not None
    assert found.id == mock_id
    assert found.response_body == {"message": "hello"}

    # Find by ID
    found_by_id = await repo.find_by_id(mock_id)
    assert found_by_id is not None
    assert found_by_id.path == "/test"

    # Find All
    all_mocks = await repo.find_all()
    assert len(all_mocks) >= 1

    # Delete
    deleted = await repo.delete(mock_id)
    assert deleted is True

    # Verify deletion
    found_after = await repo.find(HttpMethod.GET, "/test")
    assert found_after is None

    found_by_id_after = await repo.find_by_id(mock_id)
    assert found_by_id_after is None
