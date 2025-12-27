from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from planned.core.exceptions import exceptions
from planned.domain.entities.base import BaseConfigObject
from planned.infrastructure.database import get_engine

from .mappers import row_to_entity
from .repository import BaseRepository

ConfigObjectType = TypeVar(
    "ConfigObjectType",
    bound=BaseConfigObject,
)


class BaseConfigRepository(BaseRepository[ConfigObjectType]):
    """Base repository for config objects using async SQLAlchemy Core."""
    
    Object: type[ConfigObjectType]
    table: "Table"  # type: ignore[name-defined]  # noqa: F821
    
    def _get_engine(self) -> AsyncEngine:
        """Get the database engine."""
        return get_engine()

    async def get(self, key: str) -> ConfigObjectType:
        """Get an object by key."""
        engine = self._get_engine()
        async with engine.connect() as conn:
            stmt = select(self.table).where(self.table.c.id == key)
            result = await conn.execute(stmt)
            row = result.mapping().first()
            
            if row is None:
                raise exceptions.NotFoundError(
                    f"`{self.Object.__name__}` with key '{key}' not found.",
                )
            
            return row_to_entity(dict(row), self.Object)

    async def all(self) -> list[ConfigObjectType]:
        """Get all objects."""
        engine = self._get_engine()
        async with engine.connect() as conn:
            stmt = select(self.table)
            result = await conn.execute(stmt)
            rows = result.mappings().all()
            
            return [row_to_entity(dict(row), self.Object) for row in rows]
