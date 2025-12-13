import asyncio
import os
import sys

# Add project root to python path to allow importing src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine

from src.config import get_settings
from src.infrastructure.persistence.postgres.models import Base


async def init_postgres() -> None:
    """
    Initialize PostgreSQL tables for local development.
    """
    settings = get_settings()

    # DSNが設定されていない場合のフォールバック
    database_url = (
        settings.postgres_dsn or "postgresql+asyncpg://user:pass@localhost/db"
    )

    print(f"Connecting to PostgreSQL at {database_url}...")

    engine = create_async_engine(database_url, echo=True)

    try:
        async with engine.begin() as conn:
            print("Creating tables...")
            # 既存のテーブルを削除して作り直す場合は drop_all を有効にする
            # /await conn.run_sync(Base.metadata.drop_all)/
            await conn.run_sync(Base.metadata.create_all)
            print("Tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_postgres())
