from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.domain.mocks.repository import MockRepository
from src.domain.mocks.services import MockManagementService, MockSimulatorService
from src.domain.mocks.template_engine import TemplateEngine
from src.infrastructure.dynamodb.mock_repository import DynamoMockRepository
from src.infrastructure.persistence.postgres.database import get_db_session
from src.infrastructure.persistence.postgres.repositories.mock_repository import (
    PostgresMockRepository,
)


async def get_repository(
    session: Annotated[AsyncSession | None, Depends(get_db_session)],
) -> MockRepository:
    """
    Provides an instance of the MockRepository based on configuration.
    """
    settings = get_settings()
    if settings.db_type == "postgres":
        if session is None:
            raise RuntimeError("Database session is not available")
        return PostgresMockRepository(session)
    return DynamoMockRepository()


@lru_cache
def get_template_engine() -> TemplateEngine:
    """
    Provides a singleton instance of the TemplateEngine.
    """
    return TemplateEngine()


def get_mock_mgmt_service(
    repo: Annotated[MockRepository, Depends(get_repository)],
) -> MockManagementService:
    """
    Provides an instance of MockManagementService with repository injected.
    """
    return MockManagementService(repo)


def get_mock_sim_service(
    repo: Annotated[MockRepository, Depends(get_repository)],
    template_engine: Annotated[TemplateEngine, Depends(get_template_engine)],
) -> MockSimulatorService:
    """
    Provides an instance of MockSimulatorService with repository and template engine
    injected.
    """
    return MockSimulatorService(repo, template_engine)
