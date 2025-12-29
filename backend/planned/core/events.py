"""Shared repository change event types.

These types are used by both the application and infrastructure layers,
so they live in the core module to avoid circular dependencies.
"""

from typing import Generic, Literal, Protocol, TypeVar

import pydantic

ObjectType = TypeVar("ObjectType")


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

