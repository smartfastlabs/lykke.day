"""Base types for repository protocol mixins."""

from typing import Any, Protocol, TypeVar
from uuid import UUID

T = TypeVar("T")


class ReadOnlyRepositoryProtocol(Protocol[T]):
    """Base protocol for read-only repositories.

    Provides all read operations that repositories may need:
    - get: Retrieve a single object by key
    - all: Retrieve all objects
    - search_query: Search objects based on a query object (for date-scoped queries)
    """

    async def get(self, key: UUID) -> T:
        """Get an object by key."""
        ...

    async def all(self) -> list[T]:
        """Get all objects."""
        ...

    async def search_query(self, query: object) -> list[T]:
        """Search for objects based on a query object.

        Note: Date filtering should be done using query objects with date fields.
        """
        ...


class ReadWriteRepositoryProtocol(Protocol[T]):
    """Base protocol for read-write repositories.

    Provides all read and write operations that repositories may need:
    - get: Retrieve a single object by key
    - put: Save or update an object
    - all: Retrieve all objects
    - delete: Delete an object by key or by object
    - insert_many: Insert multiple objects in a single transaction
    - search_query: Search objects based on a query object (for date-scoped queries)
    - delete_many: Delete objects matching a query
    - apply_updates: Apply partial updates to an object identified by id
    """

    async def get(self, key: UUID) -> T:
        """Get an object by key."""
        ...

    async def put(self, obj: T) -> T:
        """Save or update an object."""
        ...

    async def all(self) -> list[T]:
        """Get all objects."""
        ...

    async def delete(self, key: UUID | T) -> None:
        """Delete an object by key or by object."""
        ...

    async def insert_many(self, *objs: T) -> list[T]:
        """Insert multiple objects in a single transaction."""
        ...

    async def search_query(self, query: object) -> list[T]:
        """Search for objects based on a query object.

        Note: Date filtering should be done using query objects with date fields.
        """
        ...

    async def delete_many(self, query: object) -> None:
        """Delete objects matching a query."""
        ...

    async def apply_updates(self, key: UUID, **updates: Any) -> T:
        """Apply partial updates to an object identified by id."""
        ...
