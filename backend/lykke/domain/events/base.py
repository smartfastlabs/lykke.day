"""Base classes for domain events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any, Generic, TypeVar
from uuid import UUID

if TYPE_CHECKING:
    from lykke.domain.value_objects.update import BaseUpdateObject

    _BaseUpdateObject = BaseUpdateObject
else:
    # At runtime, we don't need the actual types for TypeVar bounds
    # The bounds are only used for type checking
    _BaseUpdateObject = Any

UpdateObjectType = TypeVar("UpdateObjectType", bound=_BaseUpdateObject)


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base class for all domain events.

    Domain events represent something important that happened in the domain.
    They are immutable and contain all the information needed to understand
    what happened.
    """

    user_id: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    entity_id: UUID | None = None
    entity_type: str | None = None
    entity_date: date | None = None  # For date-specific entities (tasks, events, days)


@dataclass(frozen=True, kw_only=True)
class EntityCreatedEvent(DomainEvent):
    """Base class for entity creation events.

    This event is raised when a new entity is created via create().
    """


@dataclass(frozen=True, kw_only=True)
class EntityDeletedEvent(DomainEvent):
    """Base class for entity deletion events.

    This event is raised when an entity is deleted via delete().
    """


@dataclass(frozen=True, kw_only=True)
class EntityUpdatedEvent(DomainEvent, Generic[UpdateObjectType]):
    """Base class for entity update events.

    This event is raised when an entity is updated via apply_update().
    It contains the update object that was applied.

    Type parameters:
        UpdateObjectType: The type of update object (e.g., DayUpdateObject)
    """

    update_object: UpdateObjectType
