"""Base classes for domain events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar
from uuid import UUID

if TYPE_CHECKING:
    from lykke.domain.entities.audit_log import AuditLogEntity
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

    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


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


class AuditedEvent(Protocol):
    """Protocol for domain events that should generate audit logs.

    Events implementing this protocol will automatically create AuditLog
    entries when processed by the Unit of Work. The event must implement
    a to_audit_log() method that returns an AuditLogEntity.

    Example:
        @dataclass(frozen=True, kw_only=True)
        class MyEvent(DomainEvent, AuditedEvent):
            task_id: UUID

            def to_audit_log(self, user_id: UUID) -> AuditLogEntity | None:
                return AuditLogEntity(
                    user_id=user_id,
                    activity_type=self.__class__.__name__,
                    entity_id=self.task_id,
                    entity_type="task",
                    meta={},
                )
    """

    def to_audit_log(self, user_id: UUID) -> "AuditLogEntity":
        """Convert this event to an AuditLogEntity.

        Args:
            user_id: The user ID for the audit log entry

        Returns:
            An AuditLogEntity instance. The entity should have create() called on it by the UOW.
        """
        ...
