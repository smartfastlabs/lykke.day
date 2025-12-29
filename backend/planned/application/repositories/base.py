"""Base types for repository protocol mixins."""

from typing import Protocol, TypeVar

from planned.common.repository_handler import ChangeHandler
from planned.domain.value_objects.repository_event import RepositoryEvent

T = TypeVar("T")


class SimpleReadRepositoryProtocol(Protocol[T]):
    """Base protocol for simple read-only repositories (get by key, get all)."""

    async def get(self, key: str) -> T:
        """Get an object by key."""
        ...

    async def all(self) -> list[T]:
        """Get all objects."""
        ...


class CrudRepositoryProtocol(Protocol[T]):
    """Base protocol for CRUD repositories (get, put, all, delete)."""

    async def get(self, key: str) -> T:
        """Get an object by key."""
        ...

    async def put(self, obj: T) -> T:
        """Save or update an object."""
        ...

    async def all(self) -> list[T]:
        """Get all objects."""
        ...

    async def delete(self, key: str | T) -> None:
        """Delete an object by key or by object."""
        ...


class BasicCrudRepositoryProtocol(Protocol[T]):
    """Base protocol for basic CRUD repositories (get, put without all)."""

    async def get(self, key: str) -> T:
        """Get an object by key."""
        ...

    async def put(self, obj: T) -> T:
        """Save or update an object."""
        ...


class DateScopedCrudRepositoryProtocol(Protocol[T]):
    """Base protocol for date-scoped CRUD repositories (get by key, put, search_query, delete, listen).

    Note: Date filtering should be done using query objects with date fields.
    """

    async def get(self, key: str) -> T:
        """Get an object by key."""
        ...

    async def put(self, obj: T) -> T:
        """Save or update an object."""
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

    def listen(self, handler: ChangeHandler[T]) -> None:
        """Register a change handler for repository events."""
        ...


class SimpleDateScopedRepositoryProtocol(Protocol[T]):
    """Base protocol for simple date-scoped repositories (get by key, put, listen)."""

    async def get(self, key: str) -> T:
        """Get an object by key."""
        ...

    async def put(self, obj: T) -> T:
        """Save or update an object."""
        ...

    def listen(self, handler: ChangeHandler[T]) -> None:
        """Register a change handler for repository events."""
        ...
