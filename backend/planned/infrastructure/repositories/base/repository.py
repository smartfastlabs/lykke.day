from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar
from uuid import UUID

from blinker import Signal
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.sql import Select

from planned.application.repositories.base import ChangeEvent, ChangeHandler
from planned.core.exceptions import exceptions
from planned.infrastructure.database import get_engine
from planned.infrastructure.database.transaction import get_transaction_connection
from planned.infrastructure.repositories.base.schema import BaseQuery

ObjectType = TypeVar("ObjectType")
QueryType = TypeVar("QueryType", bound=BaseQuery)


class BaseRepository(Generic[ObjectType, QueryType]):
    """Unified base repository with all CRUD operations using async SQLAlchemy Core.

    Type parameters:
        ObjectType: The entity type this repository manages
        QueryType: The query type for filtering/searching (must be a subclass of BaseQuery)

    Child repositories should set QueryClass class attribute to specify their custom query type.

    If user_uuid is provided, all queries are automatically filtered by that user.
    """

    signal_source: Signal
    Object: type[ObjectType]
    table: "Table"  # type: ignore[name-defined]  # noqa: F821
    QueryClass: type[QueryType]

    def __init__(self, user_uuid: UUID | None = None) -> None:
        """Initialize repository with optional user scoping.

        Args:
            user_uuid: If provided, all queries will be filtered by this user UUID.
                      If None, no user filtering is applied (for repositories like UserRepository).
        """
        self.user_uuid = user_uuid

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Initialize a class-level signal for each repository subclass.
        This ensures all instances of the same repository class share the same signal.
        """
        super().__init_subclass__(**kwargs)
        cls.signal_source = Signal()

    def listen(self, handler: ChangeHandler[ObjectType]) -> None:
        """
        Connect a handler to receive ChangeEvent[ObjectType] notifications.

        The handler should accept (sender, *, event: ChangeEvent[ObjectType]) as parameters.
        """
        type(self).signal_source.connect(handler)

    def _get_engine(self) -> AsyncEngine:
        """Get the database engine."""
        return get_engine()

    @asynccontextmanager
    async def _get_connection(self, for_write: bool = False):  # type: ignore[no-untyped-def]
        """Get a database connection, reusing active transaction if available.

        Args:
            for_write: If True, begin a transaction if no active transaction exists.
                       If False, use a read-only connection.

        Yields:
            A database connection.
        """
        # Check if there's an active transaction
        active_conn = get_transaction_connection()
        if active_conn is not None:
            # Reuse the active transaction connection
            yield active_conn
            return

        # No active transaction - create a new connection
        engine = self._get_engine()
        if for_write:
            # For write operations, begin a transaction
            async with engine.begin() as conn:
                yield conn
        else:
            # For read operations, use a regular connection
            async with engine.connect() as conn:
                yield conn

    async def get(self, key: str) -> ObjectType:
        """Get an object by key."""
        async with self._get_connection(for_write=False) as conn:
            stmt = select(self.table).where(self.table.c.id == key)

            # Add user_uuid filtering if scoped
            if self.user_uuid is not None and hasattr(self.table.c, "user_uuid"):
                stmt = stmt.where(self.table.c.user_uuid == self.user_uuid)

            result = await conn.execute(stmt)
            row = result.mappings().first()

            if row is None:
                raise exceptions.NotFoundError(
                    f"`{self.Object.__name__}` with key '{key}' not found.",
                )

            return type(self).row_to_entity(dict(row))  # type: ignore[attr-defined,no-any-return]

    def build_query(self, query: QueryType) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object.

        Subclasses can override this to add custom filtering logic.
        """
        stmt: Select[tuple] = select(self.table)

        # Add user_uuid filtering if scoped (must be first to ensure proper isolation)
        if self.user_uuid is not None and hasattr(self.table.c, "user_uuid"):
            stmt = stmt.where(self.table.c.user_uuid == self.user_uuid)

        if query.limit is not None:
            stmt = stmt.limit(query.limit)

        if query.offset:
            stmt = stmt.offset(query.offset)

        # Handle date filtering if table has created_at column
        if hasattr(self.table.c, "created_at"):
            if query.created_before:
                stmt = stmt.where(self.table.c.created_at < query.created_before)

            if query.created_after:
                stmt = stmt.where(self.table.c.created_at > query.created_after)

        # Handle ordering
        if query.order_by:
            col = getattr(self.table.c, query.order_by, None)
            if col is not None:
                if query.order_by_desc:
                    stmt = stmt.order_by(col.desc())
                else:
                    stmt = stmt.order_by(col)
        else:
            # Default ordering by id if available
            if hasattr(self.table.c, "id"):
                stmt = stmt.order_by(self.table.c.id)

        return stmt

    async def get_one(self, query: QueryType) -> ObjectType:
        """Get a single object matching the query. Raises NotFoundError if none found."""
        query.limit = None  # Ensure we get all results, then take first

        async with self._get_connection(for_write=False) as conn:
            stmt = self.build_query(query)
            result = await conn.execute(stmt)
            row = result.mappings().first()

            if row is None:
                raise exceptions.NotFoundError(
                    f"No results found for the given query in `{self.Object.__name__}`."
                )

            return type(self).row_to_entity(dict(row))  # type: ignore[attr-defined,no-any-return]

    async def get_one_or_none(self, query: QueryType) -> ObjectType | None:
        """Get a single object matching the query, or None if not found."""
        query.limit = None  # Ensure we get all results, then take first

        async with self._get_connection(for_write=False) as conn:
            stmt = self.build_query(query)
            result = await conn.execute(stmt)
            row = result.mappings().first()

            if row is None:
                return None

            return type(self).row_to_entity(dict(row))  # type: ignore[attr-defined,no-any-return]

    async def search_query(self, query: QueryType) -> list[ObjectType]:
        """Search for objects based on the provided query object."""
        async with self._get_connection(for_write=False) as conn:
            stmt = self.build_query(query)
            result = await conn.execute(stmt)
            rows = result.mappings().all()

            return [type(self).row_to_entity(dict(row)) for row in rows]  # type: ignore[attr-defined]

    async def all(self) -> list[ObjectType]:
        """Get all objects."""
        async with self._get_connection(for_write=False) as conn:
            stmt = select(self.table)

            # Add user_uuid filtering if scoped
            if self.user_uuid is not None and hasattr(self.table.c, "user_uuid"):
                stmt = stmt.where(self.table.c.user_uuid == self.user_uuid)

            result = await conn.execute(stmt)
            rows = result.mappings().all()

            return [type(self).row_to_entity(dict(row)) for row in rows]  # type: ignore[attr-defined]

    async def put(self, obj: ObjectType) -> ObjectType:
        """Save or update an object."""
        # Ensure user_uuid is set on entity if repository is user-scoped
        if self.user_uuid is not None and hasattr(obj, "user_uuid"):
            # Set user_uuid on the entity if it's not already set or doesn't match
            if not hasattr(obj, "user_uuid") or obj.user_uuid != self.user_uuid:
                obj.user_uuid = self.user_uuid

        row = type(self).entity_to_row(obj)  # type: ignore[attr-defined]

        # Ensure user_uuid is in the row if repository is user-scoped
        if (
            self.user_uuid is not None
            and "user_uuid" not in row
            and hasattr(self.table.c, "user_uuid")
        ):
            row["user_uuid"] = self.user_uuid

        async with self._get_connection(for_write=True) as conn:
            # Check if object exists (with user filtering if scoped)
            stmt = select(self.table.c.id).where(self.table.c.id == obj.id)  # type: ignore[attr-defined]
            if self.user_uuid is not None and hasattr(self.table.c, "user_uuid"):
                stmt = stmt.where(self.table.c.user_uuid == self.user_uuid)
            result = await conn.execute(stmt)
            exists = result.first() is not None

            # Use PostgreSQL INSERT ... ON CONFLICT DO UPDATE
            insert_stmt = pg_insert(self.table).values(**row)
            # Exclude only id from update
            update_dict = {k: v for k, v in row.items() if k != "id"}
            index_elements = ["id"]
            upsert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=index_elements,
                set_=update_dict,
            )
            await conn.execute(upsert_stmt)

        event_type: Literal["create", "update"] = "update" if exists else "create"
        event = ChangeEvent[ObjectType](type=event_type, value=obj)
        await self.signal_source.send_async("change", event=event)
        return obj

    async def insert_many(self, *objs: ObjectType) -> list[ObjectType]:
        """Insert multiple objects in a single transaction.

        Note: For better performance, consider batching large numbers of objects.
        """
        if not objs:
            return []

        # Ensure user_uuid is set on all entities if repository is user-scoped
        if self.user_uuid is not None:
            for obj in objs:
                if hasattr(obj, "user_uuid"):
                    obj.user_uuid = self.user_uuid

        rows = [type(self).entity_to_row(obj) for obj in objs]  # type: ignore[attr-defined]

        # Ensure user_uuid is in all rows if repository is user-scoped
        if self.user_uuid is not None and hasattr(self.table.c, "user_uuid"):
            for row in rows:
                if "user_uuid" not in row:
                    row["user_uuid"] = self.user_uuid

        async with self._get_connection(for_write=True) as conn:
            # Insert all rows - using executemany with VALUES
            for row in rows:
                insert_stmt = pg_insert(self.table).values(**row)
                await conn.execute(insert_stmt)

        # Return the objects (they should now have persisted data)
        return list(objs)

    async def apply_updates(
        self,
        key: str,
        **updates: Any,
    ) -> ObjectType:
        """Apply partial updates to an object identified by key.

        Args:
            key: The key (id) of the object to update
            **updates: Dictionary of field updates to apply

        Returns:
            The updated object
        """
        if not updates:
            # No updates to apply, just fetch and return
            return await self.get(key)

        async with self._get_connection(for_write=True) as conn:
            # Build update statement
            stmt = self.table.update().values(**updates).where(self.table.c.id == key)

            # Add user_uuid filtering if scoped
            if self.user_uuid is not None and hasattr(self.table.c, "user_uuid"):
                stmt = stmt.where(self.table.c.user_uuid == self.user_uuid)

            # Execute update
            await conn.execute(stmt)

        # Fetch and return updated object
        return await self.get(key)

    async def delete_many(self, query: QueryType) -> None:
        """Delete objects based on the provided query."""
        async with self._get_connection(for_write=True) as conn:
            # Build the select query to get the where clause
            select_stmt = self.build_query(query)
            # Remove limit/offset/order_by from delete (only keep where clause)
            where_clause = getattr(select_stmt, "whereclause", None)

            # Build delete statement
            stmt = delete(self.table)
            if where_clause is not None:
                stmt = stmt.where(where_clause)

            await conn.execute(stmt)

    async def delete_one(self, query: QueryType) -> None:
        """Delete a single object matching the query. Raises Exception if multiple match."""
        # First, get the object to ensure exactly one matches
        obj = await self.get_one(query)

        # Then delete it by key
        await self.delete(obj)

    async def delete(self, key: str | ObjectType) -> None:
        """Delete an object by key or by object."""
        # Handle both key (str) and object deletion
        if isinstance(key, str):
            # Get object before deleting for event
            try:
                obj = await self.get(key)
            except exceptions.NotFoundError:
                # If not found, nothing to delete
                return

            async with self._get_connection(for_write=True) as conn:
                stmt = delete(self.table).where(self.table.c.id == key)
                # Add user_uuid filtering if scoped
                if self.user_uuid is not None and hasattr(self.table.c, "user_uuid"):
                    stmt = stmt.where(self.table.c.user_uuid == self.user_uuid)
                await conn.execute(stmt)
        else:
            # key is actually the object
            obj = key
            async with self._get_connection(for_write=True) as conn:
                stmt = delete(self.table).where(self.table.c.id == obj.id)  # type: ignore[attr-defined]
                # Add user_uuid filtering if scoped
                if self.user_uuid is not None and hasattr(self.table.c, "user_uuid"):
                    stmt = stmt.where(self.table.c.user_uuid == self.user_uuid)
                await conn.execute(stmt)

        event = ChangeEvent[ObjectType](type="delete", value=obj)
        await self.signal_source.send_async("change", event=event)
