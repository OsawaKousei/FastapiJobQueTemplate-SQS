import asyncio
from typing import Optional

from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

from src.domain.mocks.schemas import HttpMethod, MockEndpoint
from src.infrastructure.dynamodb.client import get_table
from src.infrastructure.dynamodb.converters import to_domain, to_item


class DynamoMockRepository:
    """
    DynamoDB implementation for MockEndpoint.
    Uses Multi-Table/Document approach.
    Table Schema:
      - PK: method (String)
      - SK: path (String)
    """

    def __init__(self, table_name: str = "MockTable") -> None:
        self._table = get_table(table_name)

    async def save(self, mock: MockEndpoint) -> None:
        # ドメインモデルをそのままJSONライクに保存（埋め込み）
        item = to_item(mock)
        await asyncio.to_thread(self._table.put_item, Item=item)

    async def find(self, method: HttpMethod, path: str) -> Optional[MockEndpoint]:
        # PK/SK 文字列構築ロジックが消え、直感的なキー指定になる
        key = {"method": method.value, "path": path}

        response = await asyncio.to_thread(self._table.get_item, Key=key)
        item = response.get("Item")

        if item:
            return to_domain(item)
        return None

    async def find_by_id(self, mock_id: str) -> Optional[MockEndpoint]:
        # GSIがないため、Scanを使用（Mockデータは少量なので許容）
        # ※大量データならGSIの追加を検討するが、今回はシンプルさを優先
        response = await asyncio.to_thread(
            self._table.scan, FilterExpression=Attr("id").eq(mock_id)
        )
        items = response.get("Items", [])
        if items:
            return to_domain(items[0])
        return None

    async def delete(self, mock_id: str) -> bool:
        # IDしかわからない場合、まずPK/SKを特定する必要がある
        mock = await self.find_by_id(mock_id)
        if not mock:
            return False

        key = {"method": mock.method.value, "path": mock.path}

        try:
            await asyncio.to_thread(self._table.delete_item, Key=key)
            return True
        except ClientError:
            # ログ出力などをここで行う
            return False

    async def find_all(self) -> list[MockEndpoint]:
        response = await asyncio.to_thread(self._table.scan)
        items = response.get("Items", [])
        return [to_domain(item) for item in items]
