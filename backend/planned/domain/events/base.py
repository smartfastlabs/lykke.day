"""Base classes for domain events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Generic, TypeVar

if TYPE_CHECKING:
    from planned.domain.entities.base import BaseEntityObject
    from planned.domain.value_objects.update import BaseUpdateObject
    _BaseUpdateObject = BaseUpdateObject
    _BaseEntityObject = BaseEntityObject
else:
    # At runtime, we don't need the actual types for TypeVar bounds
    # The bounds are only used for type checking
    _BaseUpdateObject = Any
    _BaseEntityObject = Any

UpdateObjectType = TypeVar("UpdateObjectType", bound=_BaseUpdateObject)
EntityType = TypeVar("EntityType", bound=_BaseEntityObject)


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base class for all domain events.

    Domain events represent something important that happened in the domain.
    They are immutable and contain all the information needed to understand
    what happened.
    """

    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, kw_only=True)
class EntityUpdatedEvent(DomainEvent, Generic[UpdateObjectType, EntityType]):
    """Base class for entity update events.

    This event is raised when an entity is updated via apply_update().
    It contains the update object that was applied and the new entity state.

    Type parameters:
        UpdateObjectType: The type of update object (e.g., DayUpdateObject)
        EntityType: The type of entity that was updated (e.g., DayEntity)
    """

    update_object: UpdateObjectType
    entity: EntityType
