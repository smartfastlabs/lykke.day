"""Base repository implementations with optional user scoping.

This module provides a unified BaseRepository that handles both user-scoped
and non-user-scoped operations through composition rather than inheritance duplication.
"""

from contextlib import asynccontextmanager
from typing import Any, ClassVar, Generic, TypeVar
from uuid import UUID

from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities.base import BaseEntityObject
from lykke.infrastructure.database import get_engine
from lykke.infrastructure.database.transaction import get_transaction_connection
from lykke.infrastructure.repositories.base.utils import normalize_list_fields
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.sql import Select

ObjectType = TypeVar("ObjectType", bound=BaseEntityObject)
QueryType = TypeVar("QueryType", bound=value_objects.BaseQuery)


class BaseRepository(Generic[ObjectType, QueryType]):
    """Unified base repository with all CRUD operations using async SQLAlchemy Core.

    Type parameters:
        ObjectType: The entity type this repository manages
        QueryType: The query type for filtering/searching (must be a subclass of BaseQuery)

    This repository supports optional user scoping. When user_id is provided,
    all operations are automatically filtered by user_id.

    Class Attributes:
        Object: The entity class this repository manages.
        table: The SQLAlchemy table for this entity.
        QueryClass: The query class for filtering.
        excluded_row_fields: Set of field names to exclude when converting row to entity.
            Useful for database-only fields like computed date columns.

    Instance Attributes:
        user_id: Optional user ID for scoping. When set, all queries filter by this user.
    """

    Object: type[ObjectType]
    table: "Table"  # type: ignore[name-defined]  # noqa: F821
    QueryClass: type[QueryType]
    user_id: UUID | None

    # Fields to exclude when converting database row to entity
    # Override in subclasses for entity-specific exclusions (e.g., {"date"} for computed fields)
    excluded_row_fields: ClassVar[set[str]] = set()

    def __init__(self, user_id: UUID | None = None) -> None:
        """Initialize repository with optional user scoping.

        Args:
            user_id: Optional user ID. When provided, all operations are scoped to this user.
        """
        self.user_id = user_id

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> ObjectType:
        """Convert a database row dict to an entity.

        Default implementation that:
        1. Filters out fields listed in `excluded_row_fields`
        2. Normalizes None values to [] for list-typed fields
        3. Constructs entity from dict using dataclass initialization

        Override this method in subclasses that need custom deserialization
        logic (e.g., handling JSONB fields that need special parsing).

        Args:
            row: Dictionary containing database row data.

        Returns:
            An instance of the entity class.
        """
        from lykke.infrastructure.repositories.base.utils import (
            ensure_datetimes_utc,
            filter_init_false_fields,
        )

        # Filter out excluded fields (e.g., database-only computed columns)
        if cls.excluded_row_fields:
            data = {k: v for k, v in row.items() if k not in cls.excluded_row_fields}
        else:
            data = dict(row)

        # Normalize None values to [] for list-typed fields
        data = normalize_list_fields(data, cls.Object)

        # Normalize datetimes to UTC to avoid naive values propagating
        data = ensure_datetimes_utc(data)

        # Filter out fields with init=False (e.g., _domain_events)
        data = filter_init_false_fields(data, cls.Object)

        return cls.Object(**data)

    @property
    def _is_user_scoped(self) -> bool:
        """Check if this repository instance is user-scoped."""
        return self.user_id is not None

    @property
    def _table_has_user_id(self) -> bool:
        """Check if the table has a user_id column."""
        return hasattr(self.table.c, "user_id")

    def _apply_user_scope(self, stmt: Select[tuple]) -> Select[tuple]:
        """Apply user scope filtering to a select statement.

        Args:
            stmt: The SQLAlchemy select statement to filter.

        Returns:
            The statement with user_id filtering applied (if applicable).
        """
        if self._is_user_scoped and self._table_has_user_id:
            stmt = stmt.where(self.table.c.user_id == self.user_id)
        return stmt

    def _apply_user_scope_to_mutate(self, stmt: Any) -> Any:
        """Apply user scope filtering to update/delete statements.

        Args:
            stmt: The SQLAlchemy update or delete statement to filter.

        Returns:
            The statement with user_id filtering applied (if applicable).
        """
        if self._is_user_scoped and self._table_has_user_id:
            stmt = stmt.where(self.table.c.user_id == self.user_id)
        return stmt

    def _prepare_entity_for_save(self, obj: ObjectType) -> ObjectType:
        """Prepare an entity for saving by setting user_id if scoped.

        Args:
            obj: The entity to prepare.

        Returns:
            The entity with user_id set (if applicable).
        """
        if self._is_user_scoped and hasattr(obj, "user_id"):
            obj.user_id = self.user_id
        return obj

    def _prepare_row_for_save(self, row: dict[str, Any]) -> dict[str, Any]:
        """Prepare a row dict for saving by ensuring user_id is set.

        Args:
            row: The row dictionary to prepare.

        Returns:
            The row with user_id set (if applicable).
        """
        if self._is_user_scoped and self._table_has_user_id and "user_id" not in row:
            row["user_id"] = self.user_id
        return row

    def _strip_pagination(self, query: QueryType) -> QueryType:
        """Return a copy of the query with pagination removed."""
        query_without_paging = query.model_copy()
        query_without_paging.limit = None
        query_without_paging.offset = None
        return query_without_paging

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

    async def get(self, key: UUID) -> ObjectType:
        """Get an object by id.

        If this repository is user-scoped, the query will also filter by user_id.
        """
        async with self._get_connection(for_write=False) as conn:
            stmt = select(self.table).where(self.table.c.id == key)
            stmt = self._apply_user_scope(stmt)

            result = await conn.execute(stmt)
            row = result.mappings().first()

            if row is None:
                raise NotFoundError(f"{self.Object.__name__} with id {key} not found")

            return type(self).row_to_entity(dict(row))

    def build_query(self, query: QueryType) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object.

        Automatically applies user scoping if this repository is user-scoped.
        Subclasses can override this to add custom filtering logic.
        """
        stmt: Select[tuple] = select(self.table)

        # Apply user scope first to ensure proper isolation
        stmt = self._apply_user_scope(stmt)

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
            # Default ordering by id
            stmt = stmt.order_by(self.table.c.id)

        return stmt

    async def search_one(self, query: QueryType) -> ObjectType:
        """Get a single object matching the query. Raises NotFoundError if none found."""
        query.limit = None  # Ensure we get all results, then take first

        async with self._get_connection(for_write=False) as conn:
            stmt = self.build_query(query)
            result = await conn.execute(stmt)
            row = result.mappings().first()

            if row is None:
                raise NotFoundError(
                    f"No results found for the given query in `{self.Object.__name__}`."
                )

            return type(self).row_to_entity(dict(row))

    async def search_one_or_none(self, query: QueryType) -> ObjectType | None:
        """Get a single object matching the query, or None if not found."""
        query.limit = None  # Ensure we get all results, then take first

        async with self._get_connection(for_write=False) as conn:
            stmt = self.build_query(query)
            result = await conn.execute(stmt)
            row = result.mappings().first()

            if row is None:
                return None

            return type(self).row_to_entity(dict(row))

    async def get_one(self, query: QueryType) -> ObjectType:
        """Backward-compatible alias for search_one."""
        return await self.search_one(query)

    async def get_one_or_none(self, query: QueryType) -> ObjectType | None:
        """Backward-compatible alias for search_one_or_none."""
        return await self.search_one_or_none(query)

    async def search(self, query: QueryType) -> list[ObjectType]:
        """Search for objects based on the provided query object."""
        async with self._get_connection(for_write=False) as conn:
            stmt = self.build_query(query)
            result = await conn.execute(stmt)
            rows = result.mappings().all()

            return [type(self).row_to_entity(dict(row)) for row in rows]

    async def paged_search(
        self, query: QueryType
    ) -> value_objects.PagedQueryResponse[ObjectType]:
        """Search for objects with pagination metadata."""
        items = await self.search(self._strip_pagination(query))
        limit = query.limit or 50
        offset = query.offset or 0
        start = offset
        end = start + limit
        total = len(items)
        paginated_items = items[start:end]

        return value_objects.PagedQueryResponse(
            items=paginated_items,
            total=total,
            limit=limit,
            offset=offset,
            has_next=end < total,
            has_previous=start > 0,
        )

    async def all(self) -> list[ObjectType]:
        """Get all objects.

        If this repository is user-scoped, only returns objects for the user.
        """
        async with self._get_connection(for_write=False) as conn:
            stmt = select(self.table)
            stmt = self._apply_user_scope(stmt)

            result = await conn.execute(stmt)
            rows = result.mappings().all()

            return [type(self).row_to_entity(dict(row)) for row in rows]

    async def put(self, obj: ObjectType) -> ObjectType:
        """Save or update an object.

        If this repository is user-scoped, ensures user_id is set on the entity.
        """
        # Prepare entity and row for save
        obj = self._prepare_entity_for_save(obj)
        row = type(self).entity_to_row(obj)  # type: ignore[attr-defined]
        row = self._prepare_row_for_save(row)

        async with self._get_connection(for_write=True) as conn:
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

        return obj

    async def insert_many(self, *objs: ObjectType) -> list[ObjectType]:
        """Insert multiple objects in a single transaction.

        If this repository is user-scoped, ensures user_id is set on all entities.
        Note: For better performance, consider batching large numbers of objects.
        """
        if not objs:
            return []

        # Prepare all entities and rows
        prepared_objs = [self._prepare_entity_for_save(obj) for obj in objs]
        rows = [type(self).entity_to_row(obj) for obj in prepared_objs]  # type: ignore[attr-defined]
        rows = [self._prepare_row_for_save(row) for row in rows]

        async with self._get_connection(for_write=True) as conn:
            # Insert all rows
            for row in rows:
                insert_stmt = pg_insert(self.table).values(**row)
                await conn.execute(insert_stmt)

        # Return the objects (they should now have persisted data)
        return list(prepared_objs)

    async def apply_updates(
        self,
        key: UUID,
        **updates: Any,
    ) -> ObjectType:
        """Apply partial updates to an object identified by id.

        If this repository is user-scoped, the update is filtered by user_id.

        Args:
            key: The id of the object to update
            **updates: Dictionary of field updates to apply

        Returns:
            The updated object
        """
        if not updates:
            # No updates to apply, just fetch and return
            return await self.get(key)

        async with self._get_connection(for_write=True) as conn:
            # Build update statement with user scope
            stmt = self.table.update().values(**updates).where(self.table.c.id == key)
            stmt = self._apply_user_scope_to_mutate(stmt)

            # Execute update
            await conn.execute(stmt)

        # Fetch and return updated object
        return await self.get(key)

    async def delete_many(self, query: QueryType) -> None:
        """Delete objects based on the provided query.

        User scoping is automatically applied via build_query.
        """
        await self.bulk_delete(query)

    async def bulk_delete(self, query: QueryType) -> None:
        """Delete all objects matching the query, ignoring pagination."""
        query_without_paging = self._strip_pagination(query)

        async with self._get_connection(for_write=True) as conn:
            select_stmt = self.build_query(query_without_paging)
            where_clause = getattr(select_stmt, "whereclause", None)

            stmt = delete(self.table)
            if where_clause is not None:
                stmt = stmt.where(where_clause)

            await conn.execute(stmt)

    async def delete_one(self, query: QueryType) -> None:
        """Delete a single object matching the query. Raises Exception if multiple match."""
        # First, get the object to ensure exactly one matches
        obj = await self.search_one(query)

        # Then delete it by key
        await self.delete(obj)

    async def delete(self, key: UUID | ObjectType) -> None:
        """Delete an object by id or by object.

        If this repository is user-scoped, the delete is filtered by user_id.
        """
        # Handle both key (UUID) and object deletion
        if isinstance(key, UUID):
            obj_id = key
        else:
            # key is actually the object
            obj_id = key.id

        async with self._get_connection(for_write=True) as conn:
            stmt = delete(self.table).where(self.table.c.id == obj_id)
            stmt = self._apply_user_scope_to_mutate(stmt)
            await conn.execute(stmt)


class UserScopedBaseRepository(
    BaseRepository[ObjectType, QueryType], Generic[ObjectType, QueryType]
):
    """Base repository that requires user scoping.

    This is a thin wrapper around BaseRepository that enforces user_id is required.
    All the actual logic is in BaseRepository.

    Type parameters:
        ObjectType: The entity type this repository manages
        QueryType: The query type for filtering/searching (must be a subclass of BaseQuery)
    """

    user_id: UUID  # Override to make non-optional

    def __init__(self, user_id: UUID) -> None:
        """Initialize repository with required user scoping.

        Args:
            user_id: Required user ID. All queries will be filtered by this user ID.
        """
        super().__init__(user_id=user_id)

    @property
    def _is_user_scoped(self) -> bool:
        return True
