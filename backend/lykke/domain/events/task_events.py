"""Domain events related to Task aggregates."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from lykke.domain.entities import AuditLogEntity
from lykke.domain.value_objects import ActivityType, TaskStatus
from lykke.domain.value_objects.update import TaskDefinitionUpdateObject

from .base import AuditedEvent, DomainEvent, EntityUpdatedEvent

__all__ = [
    "TaskActionRecordedEvent",
    "TaskCompletedEvent",
    "TaskCreatedEvent",
    "TaskDefinitionUpdatedEvent",
    "TaskPuntedEvent",
    "TaskStateUpdatedEvent",
    "TaskStatusChangedEvent",
]


@dataclass(frozen=True, kw_only=True)
class TaskCreatedEvent(DomainEvent):
    """Event raised when a task is created."""

    task_id: UUID
    user_id: UUID
    name: str


@dataclass(frozen=True, kw_only=True)
class TaskStatusChangedEvent(DomainEvent):
    """Event raised when a task's status changes."""
    
    task_id: UUID
    old_status: str
    new_status: str


@dataclass(frozen=True, kw_only=True)
class TaskPuntedEvent(DomainEvent, AuditedEvent):
    """Event raised when a task is punted.
    
    This event is specifically for PUNT status changes and always creates an audit log.
    """

    task_id: UUID
    old_status: str

    def to_audit_log(self, user_id: UUID) -> AuditLogEntity:
        """Create audit log for task punt.

        Returns:
            AuditLogEntity for task punt.
        """
        return AuditLogEntity(
            user_id=user_id,
            activity_type=ActivityType.TASK_PUNTED,
            entity_id=self.task_id,
            entity_type="task",
            meta={
                "old_status": self.old_status,
                "new_status": TaskStatus.PUNT.value,
            },
        )


@dataclass(frozen=True, kw_only=True)
class TaskCompletedEvent(DomainEvent, AuditedEvent):
    """Event raised when a task is completed."""

    task_id: UUID
    completed_at: str  # ISO format datetime string

    def to_audit_log(self, user_id: UUID) -> AuditLogEntity:
        """Create audit log for task completion.

        Returns:
            AuditLogEntity for task completion.
        """
        return AuditLogEntity(
            user_id=user_id,
            activity_type=ActivityType.TASK_COMPLETED,
            entity_id=self.task_id,
            entity_type="task",
            meta={"completed_at": self.completed_at},
        )


@dataclass(frozen=True, kw_only=True)
class TaskActionRecordedEvent(DomainEvent):
    """Event raised when an action is recorded on a task."""

    task_id: UUID
    action_type: str


@dataclass(frozen=True, kw_only=True)
class TaskStateUpdatedEvent(DomainEvent):
    """Event raised whenever a task's state mutates.

    Used to ensure the task aggregate always emits an event when updated.
    """

    task_id: UUID
    action_type: str
    old_status: str
    new_status: str
    completed_at: str | None


@dataclass(frozen=True, kw_only=True)
class TaskDefinitionUpdatedEvent(EntityUpdatedEvent[TaskDefinitionUpdateObject]):
    """Event raised when a task definition is updated via apply_update()."""
