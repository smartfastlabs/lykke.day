"""Base classes for domain events."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime, time
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, TypeVar
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


class AuditableDomainEvent:
    """Mixin class for domain events that should generate persistent audit logs.

    Events inheriting from this class will automatically create AuditLogEntity
    records when processed by the Unit of Work. These audit logs are:
    - Stored in the database permanently
    - Broadcast to Redis for real-time client updates
    - Visible to users in their activity timeline

    Use this mixin when:
    - User would want to see this action in their activity timeline
    - Action represents a deliberate user choice or significant milestone
    - You need persistent history of this action
    - Examples: task completed, brain dump added, message sent

    Don't use for:
    - Internal state tracking (e.g., TaskStateUpdatedEvent)
    - System-triggered updates (e.g., automatic recalculations)
    - Low-level CRUD operations handled by AuditableEntity
    - Configuration changes (e.g., updating templates)

    The default implementation extracts all event fields into the audit log's
    meta field and infers entity_id and entity_type from the event's fields.

    Example:
        @dataclass(frozen=True, kw_only=True)
        class TaskCompletedEvent(DomainEvent, AuditableDomainEvent):
            task_id: UUID
            completed_at: datetime

        # Automatically creates audit log with:
        # - activity_type: "TaskCompletedEvent"
        # - entity_id: task_id
        # - entity_type: "task" (inferred from "task_id")
        # - meta: {"task_id": "...", "completed_at": "..."}
        # - Stored in database
        # - Broadcast to clients via WebSocket
    """

    def to_audit_log(self, user_id: UUID) -> AuditLogEntity:
        """Convert this event to an AuditLogEntity.

        The default implementation:
        - Uses the event class name as activity_type
        - Extracts all event fields into meta
        - Infers entity_id from fields ending in "_id" (excluding "user_id")
        - Infers entity_type from the entity_id field name

        Args:
            user_id: The user ID for the audit log entry

        Returns:
            An AuditLogEntity instance. The entity should have create() called on it by the UOW.
        """
        from typing import cast

        from lykke.domain.entities.audit_log import AuditLogEntity

        # Get all event fields as a dict
        # All events are dataclasses, so use asdict() to handle nested structures properly
        # Cast to Any to satisfy mypy - we know it's a dataclass instance
        event_dict = asdict(cast("Any", self))

        # Convert to JSON-serializable format
        # Serialize each value in the dict to handle datetime, UUID, etc.
        json_safe_meta: dict[str, Any] = {}
        for key, value in event_dict.items():
            if isinstance(value, (datetime, date, time)):
                json_safe_meta[key] = value.isoformat()
            elif isinstance(value, UUID):
                json_safe_meta[key] = str(value)
            elif isinstance(value, Enum):
                json_safe_meta[key] = value.value
            elif isinstance(value, dict):
                json_safe_meta[key] = {
                    k: (
                        v.isoformat()
                        if isinstance(v, (datetime, date, time))
                        else str(v)
                        if isinstance(v, UUID)
                        else v.value
                        if isinstance(v, Enum)
                        else v
                    )
                    for k, v in value.items()
                }
            elif isinstance(value, list):
                json_safe_meta[key] = [
                    (
                        item.isoformat()
                        if isinstance(item, (datetime, date, time))
                        else str(item)
                        if isinstance(item, UUID)
                        else item.value
                        if isinstance(item, Enum)
                        else item
                    )
                    for item in value
                ]
            else:
                json_safe_meta[key] = value

        # Find entity_id by looking for fields ending in "_id" (excluding "user_id")
        # Use original event_dict to get UUID objects, not string versions
        entity_id: UUID | None = None
        entity_type: str | None = None

        for field_name, field_value in event_dict.items():
            if (
                field_name.endswith("_id")
                and field_name != "user_id"
                and isinstance(field_value, UUID)
            ):
                # Use the first matching field as entity_id
                entity_id = field_value
                # Infer entity_type from field name (e.g., "task_id" -> "task")
                entity_type = field_name[:-3]  # Remove "_id" suffix
                break

        # Create audit log with all event data in meta (JSON-serializable)
        return AuditLogEntity(
            user_id=user_id,
            activity_type=self.__class__.__name__,
            entity_id=entity_id,
            entity_type=entity_type,
            meta=json_safe_meta,
        )
