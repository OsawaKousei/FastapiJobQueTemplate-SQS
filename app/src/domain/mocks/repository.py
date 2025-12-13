from typing import Protocol

from src.domain.mocks.schemas import HttpMethod, MockEndpoint


class MockRepository(Protocol):
    async def save(self, mock: MockEndpoint) -> None:
        """モック定義を保存する"""
        ...

    async def find(self, method: HttpMethod, path: str) -> MockEndpoint | None:
        """メソッドとパスでモックを検索する"""
        ...

    async def delete(self, mock_id: str) -> bool:
        """IDでモックを削除する。削除できた場合はTrueを返す"""
        ...

    async def find_by_id(self, mock_id: str) -> MockEndpoint | None:
        """IDでモックを検索する"""
        ...

    async def find_all(self) -> list[MockEndpoint]:
        """全てのモックを取得する"""
        ...
