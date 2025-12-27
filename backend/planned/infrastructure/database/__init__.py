"""Database connection and engine management."""

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from planned.core.config import settings

# Global async engine instance
_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Get or create the global async database engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            echo=settings.DEBUG,
        )
    return _engine


async def close_engine() -> None:
    """Close the global database engine."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None

