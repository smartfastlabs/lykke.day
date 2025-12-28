"""Base types for repository change events and common repository protocol mixins."""

import datetime
from typing import Generic, Literal, Protocol, TypeVar

import pydantic

ObjectType = TypeVar("ObjectType")
T = TypeVar("T")


class ChangeEvent(pydantic.BaseModel, Generic[ObjectType]):
    """Represents a change event for a repository object."""

    type: Literal["create", "update", "delete"]
    value: ObjectType

    model_config = pydantic.ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class ChangeHandler(Protocol[ObjectType]):
    """Protocol for handling repository change events."""

    async def __call__(
        self, _sender: object | None = None, *, event: ChangeEvent[ObjectType]
    ) -> None:
        """Handle a change event.

        Args:
            _sender: The sender of the event (optional).
            event: The change event containing the type and value.
        """
        ...


class SimpleReadRepositoryProtocol(Protocol[T]):
    """Base protocol for simple read-only repositories (get by key, get all)."""

    async def get(self, key: str) -> T:
        """Get an object by key."""
        ...

    async def all(self) -> list[T]:
        """Get all objects."""
        ...


class CrudRepositoryProtocol(Protocol[T]):
    """Base protocol for CRUD repositories (get, put, all)."""

    async def get(self, key: str) -> T:
        """Get an object by key."""
        ...

    async def put(self, obj: T) -> T:
        """Save or update an object."""
        ...

    async def all(self) -> list[T]:
        """Get all objects."""
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
    """Base protocol for date-scoped CRUD repositories (get by date+key, put, search, delete, listen)."""

    async def get(self, date: datetime.date, key: str) -> T:
        """Get an object by date and key."""
        ...

    async def put(self, obj: T) -> T:
        """Save or update an object."""
        ...

    async def search(self, date: datetime.date) -> list[T]:
        """Search for objects on a specific date."""
        ...

    async def delete(self, obj: T) -> None:
        """Delete an object."""
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

