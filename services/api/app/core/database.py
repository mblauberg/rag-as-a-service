"""Async database connection and session management."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Create async engine with conditional pool settings
# SQLite doesn't support pool_size and max_overflow
engine_kwargs = {
    "echo": False,
    "future": True,
}

# Only add pool settings for non-SQLite databases
if "sqlite" not in settings.database_url:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = 10  # type: ignore[assignment]
    engine_kwargs["max_overflow"] = 20  # type: ignore[assignment]

engine = create_async_engine(settings.database_url, **engine_kwargs)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create declarative base for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession]:
    """
    Dependency that provides an async database session with transaction management.

    This dependency ensures that:
    - Each request gets its own database session
    - Transactions are committed on success (explicit commit required in service layer)
    - Transactions are rolled back on error
    - Sessions are properly closed

    Yields:
        AsyncSession: Database session for the request
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """
    Initialize database by creating all tables.
    Note: In production, use proper migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
