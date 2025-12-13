import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine

from src.config import Settings, get_settings
from src.infrastructure.persistence.postgres.models import Base
from src.main import app


@pytest.fixture(scope="module", autouse=True)
async def setup_postgres_db():
    """
    テスト実行前にPostgreSQLのテーブルを作成し、終了後に削除する
    """
    os.environ["DB_TYPE"] = "postgres"
    get_settings.cache_clear()

    settings = get_settings()
    database_url = (
        settings.postgres_dsn or "postgresql+asyncpg://user:pass@localhost/db"
    )
    engine = create_async_engine(database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    os.environ["DB_TYPE"] = "dynamodb"
    get_settings.cache_clear()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def client():
    # 設定をオーバーライドしてPostgreSQLを使用するように強制する
    # get_settingsはlru_cacheされているため、cache_clear()が必要かもしれないが、
    # dependency_overridesを使うのが確実

    settings = get_settings()
    database_url = (
        settings.postgres_dsn or "postgresql+asyncpg://user:pass@localhost/db"
    )

    def get_test_settings():
        return Settings(
            db_type="postgres",
            postgres_dsn=database_url,
            dynamodb_endpoint_url=settings.dynamodb_endpoint_url,
        )

    app.dependency_overrides[get_settings] = get_test_settings

    # src.dependencies.get_repository 内で get_settings() が直接呼ばれている場合、
    # dependency_overrides は効かない可能性がある。
    # しかし、今回の実装では src/dependencies.py で get_settings() を呼んでいる。
    # テスト実行時に環境変数をセットするか、mockを使う必要がある。
    # ここではシンプルにget_settingsのキャッシュをクリアして環境変数を一時的に変更する。

    # 最も確実なのは、TestClient作成前に環境変数をセットし、キャッシュをクリアすること。
    import os

    os.environ["DB_TYPE"] = "postgres"
    get_settings.cache_clear()

    with TestClient(app) as c:
        yield c

    # クリーンアップ
    os.environ["DB_TYPE"] = "dynamodb"  # デフォルトに戻す
    get_settings.cache_clear()
    app.dependency_overrides.clear()


def test_e2e_mock_lifecycle_postgres(client):
    # 1. Create Mock
    mock_data = {
        "path": "/test/postgres-api",
        "method": "GET",
        "status_code": 200,
        "response_body": {"message": "Hello Postgres"},
        "headers": {"X-DB": "Postgres"},
        "latency_ms": 0,
    }
    response = client.post("/api/mocks", json=mock_data)
    assert response.status_code == 201
    created_mock = response.json()
    mock_id = created_mock["id"]
    assert created_mock["path"] == "/test/postgres-api"

    # 2. Simulate Mock
    response = client.get("/test/postgres-api")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello Postgres"}
    assert response.headers["X-DB"] == "Postgres"

    # 3. Delete Mock
    response = client.delete(f"/api/mocks/{mock_id}")
    assert response.status_code == 204

    # 4. Verify Deletion (Simulation should fail)
    response = client.get("/test/postgres-api")
    assert response.status_code == 404
