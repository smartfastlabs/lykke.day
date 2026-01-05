"""Base classes for domain events."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from planned.domain.entities.base import BaseEntityObject
from planned.domain.value_objects.update import BaseUpdateObject

UpdateObjectType = TypeVar("UpdateObjectType", bound=BaseUpdateObject)
EntityType = TypeVar("EntityType", bound=BaseEntityObject)


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
