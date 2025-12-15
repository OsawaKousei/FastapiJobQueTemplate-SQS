import os

import boto3
import pytest

from common.config import get_settings


@pytest.fixture(scope="session", autouse=True)
def set_env():
    # Force settings for testing
    os.environ["DB_TYPE"] = "dynamodb"
    os.environ["AWS_ENDPOINT_URL"] = "http://db:8000"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["AWS_ACCESS_KEY_ID"] = "dummy"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "dummy"
    os.environ["TABLE_NAME"] = "TestJobs"
    get_settings.cache_clear()


@pytest.fixture(scope="function")
def dynamodb_resource():
    settings = get_settings()
    return boto3.resource(
        "dynamodb",
        endpoint_url=settings.aws_endpoint_url,
        region_name=settings.aws_default_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


@pytest.fixture(scope="function", autouse=True)
def setup_table(dynamodb_resource):
    settings = get_settings()
    table_name = settings.table_name

    # Delete table if exists
    try:
        table = dynamodb_resource.Table(table_name)
        table.delete()
        table.wait_until_not_exists()
    except dynamodb_resource.meta.client.exceptions.ResourceNotFoundException:
        pass

    # Create table
    table = dynamodb_resource.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "job_id", "KeyType": "HASH"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "job_id", "AttributeType": "S"},
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 1,
            "WriteCapacityUnits": 1,
        },
    )
    table.wait_until_exists()
    yield table
