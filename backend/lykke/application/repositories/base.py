"""Base types for repository protocol mixins."""

from dataclasses import dataclass
from typing import Any, Generic, Protocol, TypeVar
from uuid import UUID

T = TypeVar("T")


@dataclass(kw_only=True)
class PagedSearchResult(Generic[T]):
    """Paginated search result wrapper."""

    items: list[T]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool


class ReadOnlyRepositoryProtocol(Protocol[T]):
    """Base protocol for read-only repositories.

    Provides all read operations that repositories may need:
    - get: Retrieve a single object by key
    - all: Retrieve all objects
    - search: Search objects based on a query object
    - paged_search: Search objects with pagination metadata
    """

    async def get(self, key: UUID) -> T:
        """Get an object by key."""
        ...

    async def all(self) -> list[T]:
        """Get all objects."""
        ...

    async def search(self, query: object) -> list[T]:
        """Search for objects based on a query object."""
        ...

    async def paged_search(self, query: object) -> PagedSearchResult[T]:
        """Search for objects based on a query object and return pagination metadata."""
        ...

    async def search_one(self, query: object) -> T:
        """Get a single object matching the query or raise if none found."""
        ...

    async def search_one_or_none(self, query: object) -> T | None:
        """Get a single object matching the query, or None if not found."""
        ...


class ReadWriteRepositoryProtocol(Protocol[T]):
    """Base protocol for read-write repositories.

    Provides all read and write operations that repositories may need:
    - get: Retrieve a single object by key
    - put: Save or update an object
    - all: Retrieve all objects
    - delete: Delete an object by key or by object
    - insert_many: Insert multiple objects in a single transaction
    - search: Search objects based on a query object
    - paged_search: Search objects with pagination metadata
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

    async def search(self, query: object) -> list[T]:
        """Search for objects based on a query object."""
        ...

    async def paged_search(self, query: object) -> PagedSearchResult[T]:
        """Search for objects based on a query object and return pagination metadata."""
        ...

    async def search_one(self, query: object) -> T:
        """Get a single object matching the query or raise if none found."""
        ...

    async def search_one_or_none(self, query: object) -> T | None:
        """Get a single object matching the query, or None if not found."""
        ...

    async def delete_many(self, query: object) -> None:
        """Delete objects matching a query."""
        ...

    async def bulk_delete(self, query: object) -> None:
        """Delete all objects matching a query, ignoring pagination (limit/offset)."""
        ...

    async def apply_updates(self, key: UUID, **updates: Any) -> T:
        """Apply partial updates to an object identified by id."""
        ...
