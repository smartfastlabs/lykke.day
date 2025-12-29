"""Repository change handler protocol.

This protocol is used by both application and infrastructure layers
to handle repository change events.
"""

from typing import Protocol, TypeVar

from planned.domain.value_objects.repository_event import RepositoryEvent

ObjectType = TypeVar("ObjectType")


class ChangeHandler(Protocol[ObjectType]):
    """Protocol for handling repository change events."""

    async def __call__(
        self, _sender: object | None = None, *, event: RepositoryEvent[ObjectType]
    ) -> None:
        """Handle a change event.

        Args:
            _sender: The sender of the event (optional).
            event: The change event containing the type and value.
        """
        ...

