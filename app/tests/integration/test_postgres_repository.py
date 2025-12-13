import uuid

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config import get_settings
from src.domain.mocks.schemas import HttpMethod, MockEndpoint
from src.infrastructure.persistence.postgres.models import Base
from src.infrastructure.persistence.postgres.repositories.mock_repository import (
    PostgresMockRepository,
)


@pytest.fixture(scope="function", autouse=True)
def force_postgres(monkeypatch):
    """Ensure the tests run against PostgreSQL."""
    monkeypatch.setenv("DB_TYPE", "postgres")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
async def async_engine():
    settings = get_settings()
    database_url = (
        settings.postgres_dsn or "postgresql+asyncpg://user:pass@localhost/db"
    )
    engine = create_async_engine(database_url, echo=False)

    # テーブル作成
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # クリーンアップ
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def session(async_engine):
    async_session = async_sessionmaker(async_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
        # テストごとにロールバックしてクリーンな状態を保つことも可能だが、
        # ここでは明示的にデータを消すか、トランザクションロールバックパターンを使う
        # 今回はシンプルにsessionを閉じるだけにし、データは残るが、
        # テストケース側でユニークなIDを使うか、都度消す方針とする。
        # または、以下のようにトランザクションをロールバックさせる
        await session.rollback()


@pytest.mark.asyncio
async def test_postgres_repository_crud(session):
    repo = PostgresMockRepository(session)

    mock_id = str(uuid.uuid4())
    mock = MockEndpoint(
        id=mock_id,
        path="/test-postgres",
        method=HttpMethod.GET,
        status_code=200,
        response_body={"message": "hello postgres"},
        headers={"Content-Type": "application/json"},
        latency_ms=50,
    )

    # Save
    await repo.save(mock)

    # Find
    found = await repo.find(HttpMethod.GET, "/test-postgres")
    assert found is not None
    assert found.id == mock_id
    assert found.response_body == {"message": "hello postgres"}

    # Find by ID
    found_by_id = await repo.find_by_id(mock_id)
    assert found_by_id is not None
    assert found_by_id.path == "/test-postgres"

    # Find All
    all_mocks = await repo.find_all()
    assert len(all_mocks) >= 1
    assert any(m.id == mock_id for m in all_mocks)

    # Delete
    deleted = await repo.delete(mock_id)
    assert deleted is True

    # Verify deletion
    found_after = await repo.find(HttpMethod.GET, "/test-postgres")
    assert found_after is None

    found_by_id_after = await repo.find_by_id(mock_id)
    assert found_by_id_after is None
