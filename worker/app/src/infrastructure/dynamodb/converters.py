from typing import Any

from src.domain.mocks.schemas import MockEndpoint


def to_domain(item: dict[str, Any]) -> MockEndpoint:
    """
    DynamoDB Item -> Domain Model
    """
    # Itemの中身がそのままDomain Modelの構造と一致しているためシンプル
    return MockEndpoint.model_validate(item)


def to_item(mock: MockEndpoint) -> dict[str, Any]:
    """
    Domain Model -> DynamoDB Item
    """
    # PK, SK を手動で追加する必要はない。
    # MockEndpoint自体が 'method' と 'path' を持っており、
    # それがそのままDynamoDBのキーになる。
    return mock.model_dump(mode="json")
