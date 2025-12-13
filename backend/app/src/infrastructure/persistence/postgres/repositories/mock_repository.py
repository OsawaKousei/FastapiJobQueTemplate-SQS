from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.mocks.schemas import HttpMethod, MockEndpoint
from src.infrastructure.persistence.converters.orm_to_domain import to_domain, to_orm
from src.infrastructure.persistence.postgres.models import MockEndpointModel


class PostgresMockRepository:
    """
    PostgreSQL implementation of MockRepository using SQLAlchemy.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, mock: MockEndpoint) -> None:
        """
        Save or update a mock endpoint.
        Uses merge to handle both insert and update based on primary key (id).
        """
        orm_model = to_orm(mock)
        await self.session.merge(orm_model)
        await self.session.commit()

    async def find(self, method: HttpMethod, path: str) -> MockEndpoint | None:
        """
        Find a mock endpoint by method and path.
        """
        stmt = select(MockEndpointModel).where(
            MockEndpointModel.method == method.value, MockEndpointModel.path == path
        )
        result = await self.session.execute(stmt)
        orm_model = result.scalar_one_or_none()
        if orm_model:
            return to_domain(orm_model)
        return None

    async def delete(self, mock_id: str) -> bool:
        """
        Delete a mock endpoint by ID.
        Returns True if deleted, False if not found.
        """
        stmt = delete(MockEndpointModel).where(MockEndpointModel.id == mock_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def find_by_id(self, mock_id: str) -> MockEndpoint | None:
        """
        Find a mock endpoint by ID.
        """
        stmt = select(MockEndpointModel).where(MockEndpointModel.id == mock_id)
        result = await self.session.execute(stmt)
        orm_model = result.scalar_one_or_none()
        if orm_model:
            return to_domain(orm_model)
        return None

    async def find_all(self) -> list[MockEndpoint]:
        """
        Retrieve all mock endpoints.
        """
        stmt = select(MockEndpointModel)
        result = await self.session.execute(stmt)
        orm_models = result.scalars().all()
        return [to_domain(m) for m in orm_models]
