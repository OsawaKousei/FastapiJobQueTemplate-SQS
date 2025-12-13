from typing import Any

import boto3

from src.config import get_settings


def get_dynamodb_resource() -> Any:  # noqa: ANN401
    """
    DynamoDBリソースを取得する。
    設定ファイル(src.config)からエンドポイントを取得する。
    """
    settings = get_settings()
    endpoint_url = settings.dynamodb_endpoint_url

    if endpoint_url:
        return boto3.resource(
            "dynamodb",
            endpoint_url=endpoint_url,
            region_name=settings.aws_default_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
    return boto3.resource("dynamodb")


def get_table(table_name: str) -> Any:  # noqa: ANN401
    """
    DynamoDBテーブルリソースを取得する。
    """
    dynamodb = get_dynamodb_resource()
    return dynamodb.Table(table_name)
