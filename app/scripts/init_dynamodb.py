import os
import sys

# Add project root to python path to allow importing src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
from botocore.exceptions import ClientError

from src.config import get_settings


def init_dynamodb() -> None:
    """
    Initialize DynamoDB table for local development.
    Updated to match Multi-Table / Document Model design.
    """
    settings = get_settings()
    endpoint_url = settings.dynamodb_endpoint_url
    region_name = settings.aws_default_region

    print(f"Connecting to DynamoDB at {endpoint_url}...")

    dynamodb = boto3.resource(
        "dynamodb",
        endpoint_url=endpoint_url,
        region_name=region_name,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )

    table_name = "MockTable"

    try:
        table = dynamodb.Table(table_name)
        # Check if table exists
        table.load()
        print(f"Table '{table_name}' already exists.")

        return
    except ClientError:
        pass

    print(f"Creating table '{table_name}'...")

    try:
        table = dynamodb.create_table(
            TableName=table_name,
            # Terraformの設定 (hash_key="method", range_key="path") に合わせる
            KeySchema=[
                {"AttributeName": "method", "KeyType": "HASH"},
                {"AttributeName": "path", "KeyType": "RANGE"},
            ],
            # AttributeDefinitionsにはキーに使用する属性のみを定義する
            AttributeDefinitions=[
                {"AttributeName": "method", "AttributeType": "S"},
                {"AttributeName": "path", "AttributeType": "S"},
            ],
            # GSI (GlobalSecondaryIndexes) は今回の設計で削除されたため指定しない
            # Terraformの設定 (billing_mode="PAY_PER_REQUEST") に合わせる
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        print(f"Table '{table_name}' created successfully.")

    except Exception as e:
        print(f"Error creating table: {e}")


if __name__ == "__main__":
    init_dynamodb()
