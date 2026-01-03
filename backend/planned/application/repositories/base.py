"""Base types for repository protocol mixins."""

from typing import Protocol, TypeVar
from uuid import UUID

T = TypeVar("T")
T_co = TypeVar(
    "T_co", covariant=True
)  # Covariant type variable for read-only protocols


# Read-Only Base Protocols


class SimpleReadRepositoryProtocol(Protocol[T]):
    """Base protocol for simple read-only repositories (get by key, get all)."""

    async def get(self, key: UUID) -> T:
        """Get an object by key."""
        ...

    async def all(self) -> list[T]:
        """Get all objects."""
        ...


class ReadOnlyCrudRepositoryProtocol(Protocol[T]):
    """Base protocol for read-only CRUD repositories (get, all)."""

    async def get(self, key: UUID) -> T:
        """Get an object by key."""
        ...

    async def all(self) -> list[T]:
        """Get all objects."""
        ...


class ReadOnlyBasicCrudRepositoryProtocol(Protocol[T_co]):
    """Base protocol for read-only basic CRUD repositories (get only)."""

    async def get(self, key: UUID) -> T_co:
        """Get an object by key."""
        ...


class ReadOnlyDateScopedRepositoryProtocol(Protocol[T]):
    """Base protocol for read-only date-scoped repositories (get, all, search_query).

    Note: Date filtering should be done using query objects with date fields.
    """

    async def get(self, key: UUID) -> T:
        """Get an object by key."""
        ...

    async def all(self) -> list[T]:
        """Get all objects."""
        ...

    async def search_query(self, query: object) -> list[T]:
        """Search for objects based on a query object."""
        ...


class ReadOnlySimpleDateScopedRepositoryProtocol(Protocol[T_co]):
    """Base protocol for read-only simple date-scoped repositories (get only)."""

    async def get(self, key: UUID) -> T_co:
        """Get an object by key."""
        ...


# Read-Write Base Protocols


class CrudRepositoryProtocol(Protocol[T]):
    """Base protocol for CRUD repositories (get, put, all, delete)."""

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


class BasicCrudRepositoryProtocol(Protocol[T]):
    """Base protocol for basic CRUD repositories (get, put without all)."""

    async def get(self, key: UUID) -> T:
        """Get an object by key."""
        ...

    async def put(self, obj: T) -> T:
        """Save or update an object."""
        ...


class DateScopedCrudRepositoryProtocol(Protocol[T]):
    """Base protocol for date-scoped CRUD repositories (get by key, put, search_query, delete).

    Note: Date filtering should be done using query objects with date fields.
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

    async def search_query(self, query: object) -> list[T]:
        """Search for objects based on a query object."""
        ...

    async def delete(self, obj: T) -> None:
        """Delete an object."""
        ...

    async def delete_many(self, query: object) -> None:
        """Delete objects matching a query."""
        ...


class SimpleDateScopedRepositoryProtocol(Protocol[T]):
    """Base protocol for simple date-scoped repositories (get by key, put)."""

    async def get(self, key: UUID) -> T:
        """Get an object by key."""
        ...

    async def put(self, obj: T) -> T:
        """Save or update an object."""
        ...
