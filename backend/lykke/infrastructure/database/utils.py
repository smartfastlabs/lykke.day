"""Database connection and engine management."""

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from lykke.core.config import settings

# Global async engine instance
_engine: AsyncEngine | None = None

async def reset_engine() -> AsyncEngine:
    """Reset the global async database engine."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None

    return get_engine()


def get_engine() -> AsyncEngine:
    """Get or create the global async database engine."""
    global _engine
    if _engine is None:
        logger.info("Creating async engine", settings.DATABASE_URL)
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
