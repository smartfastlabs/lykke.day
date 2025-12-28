from typing import Literal

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from planned.core.exceptions import exceptions

from .config import BaseConfigRepository, ConfigObjectType
from .repository import ChangeEvent


class BaseCrudRepository(BaseConfigRepository[ConfigObjectType]):
    """Base repository with CRUD operations using async SQLAlchemy Core."""

    async def put(self, obj: ConfigObjectType) -> ConfigObjectType:
        """Save or update an object."""
        engine = self._get_engine()
        row = type(self).entity_to_row(obj)  # type: ignore[misc]

        async with engine.begin() as conn:
            # Check if object exists
            stmt = select(self.table.c.id).where(self.table.c.id == obj.id)
            result = await conn.execute(stmt)
            exists = result.first() is not None

            # Use PostgreSQL INSERT ... ON CONFLICT DO UPDATE
            insert_stmt = pg_insert(self.table).values(**row)
            update_dict = {k: v for k, v in row.items() if k != "id"}
            upsert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=["id"],
                set_=update_dict,
            )
            await conn.execute(upsert_stmt)

        event_type: Literal["create", "update"] = "update" if exists else "create"
        event = ChangeEvent[ConfigObjectType](type=event_type, value=obj)
        await self.signal_source.send_async("change", event=event)
        return obj

    async def delete(self, key: str) -> None:
        """Delete an object by key."""
        engine = self._get_engine()

        # Get object before deleting for event
        try:
            obj = await self.get(key)
        except exceptions.NotFoundError:
            # If not found, nothing to delete
            return

        async with engine.begin() as conn:
            stmt = delete(self.table).where(self.table.c.id == key)
            await conn.execute(stmt)

        event = ChangeEvent[ConfigObjectType](type="delete", value=obj)
        await self.signal_source.send_async("change", event=event)
