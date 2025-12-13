from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import get_settings

settings = get_settings()

# DSNが設定されていない場合のフォールバックは、アプリの起動を妨げないようにする
# 実際に接続が必要になった時点でエラーになる
DATABASE_URL = settings.postgres_dsn or "postgresql+asyncpg://user:pass@localhost/db"

engine = create_async_engine(DATABASE_URL, echo=settings.log_level == "DEBUG")

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession | None, None]:
    """
    Dependency Injection用のセッションプロバイダ
    """
    if settings.db_type != "postgres":
        yield None
        return

    async with AsyncSessionLocal() as session:
        yield session
