import datetime
from collections.abc import Callable
from typing import Literal, TypeVar

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncEngine

from planned.core.exceptions import exceptions
from planned.domain.entities.base import BaseDateObject
from planned.infrastructure.database import get_engine

from .repository import BaseRepository, ChangeEvent

DateObjectType = TypeVar(
    "DateObjectType",
    bound=BaseDateObject,
)


class BaseDateRepository(BaseRepository[DateObjectType]):
    """Base repository for date-scoped entities using async SQLAlchemy Core."""

    Object: type[DateObjectType]
    table: "Table"  # type: ignore[name-defined]  # noqa: F821

    def _get_engine(self) -> AsyncEngine:
        """Get the database engine."""
        return get_engine()

    async def get(self, date: datetime.date, key: str) -> DateObjectType:
        """Get an object by date and key."""
        engine = self._get_engine()
        async with engine.connect() as conn:
            stmt = select(self.table).where(
                self.table.c.date == date,
                self.table.c.id == key,
            )
            result = await conn.execute(stmt)
            row = result.mapping().first()

            if row is None:
                raise exceptions.NotFoundError(
                    f"`{self.Object.__name__}` with date '{date}' and key '{key}' not found.",
                )

            return type(self).row_to_entity(dict(row))  # type: ignore[misc]

    async def put(self, obj: DateObjectType) -> DateObjectType:
        """Save or update an object."""
        engine = self._get_engine()
        row = type(self).entity_to_row(obj)  # type: ignore[misc]

        async with engine.begin() as conn:
            # Check if object exists
            stmt = select(self.table.c.id).where(
                self.table.c.date == obj.date,
                self.table.c.id == obj.id,
            )
            result = await conn.execute(stmt)
            exists = result.first() is not None

            # Use PostgreSQL INSERT ... ON CONFLICT DO UPDATE
            insert_stmt = pg_insert(self.table).values(**row)
            update_dict = {k: v for k, v in row.items() if k not in ("id", "date")}
            upsert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=["id"],
                set_=update_dict,
            )
            await conn.execute(upsert_stmt)

        event_type: Literal["create", "update"] = "update" if exists else "create"
        event = ChangeEvent[DateObjectType](type=event_type, value=obj)
        await self.signal_source.send_async("change", event=event)
        return obj

    async def search(self, date: datetime.date) -> list[DateObjectType]:
        """Search for objects on a specific date."""
        engine = self._get_engine()
        async with engine.connect() as conn:
            stmt = select(self.table).where(self.table.c.date == date)
            result = await conn.execute(stmt)
            rows = result.mappings().all()

            return [type(self).row_to_entity(dict(row)) for row in rows]  # type: ignore[misc]

    async def delete(self, obj: DateObjectType) -> None:
        """Delete an object."""
        engine = self._get_engine()

        async with engine.begin() as conn:
            stmt = delete(self.table).where(
                self.table.c.date == obj.date,
                self.table.c.id == obj.id,
            )
            await conn.execute(stmt)

        event = ChangeEvent[DateObjectType](type="delete", value=obj)
        await self.signal_source.send_async("change", event=event)

    async def delete_by_date(
        self,
        date: datetime.date | str,
        filter_by: Callable[[DateObjectType], bool] | None = None,
    ) -> None:
        """Delete all objects for a date, optionally filtering."""
        if isinstance(date, str):
            date = datetime.date.fromisoformat(date)

        engine = self._get_engine()

        if filter_by is None:
            # Delete all objects for the date
            async with engine.begin() as conn:
                stmt = delete(self.table).where(self.table.c.date == date)
                await conn.execute(stmt)
        else:
            # Get all objects, filter, then delete matching ones
            objects = await self.search(date)
            objects_to_delete = [obj for obj in objects if filter_by(obj)]

            if objects_to_delete:
                async with engine.begin() as conn:
                    ids_to_delete = [obj.id for obj in objects_to_delete]
                    stmt = delete(self.table).where(
                        self.table.c.date == date,
                        self.table.c.id.in_(ids_to_delete),
                    )
                    await conn.execute(stmt)

                # Send delete events for each deleted object
                for obj in objects_to_delete:
                    event = ChangeEvent[DateObjectType](type="delete", value=obj)
                    await self.signal_source.send_async("change", event=event)
