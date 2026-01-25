"""Domain events related to Task aggregates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from lykke.domain.value_objects.update import TaskDefinitionUpdateObject

from .base import AuditableDomainEvent, DomainEvent, EntityUpdatedEvent

if TYPE_CHECKING:
    from datetime import date as dt_date, datetime
    from uuid import UUID

    from lykke.domain.entities.audit_log import AuditLogEntity

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
class TaskCreatedEvent(DomainEvent, AuditableDomainEvent):
    """Event raised when a task is created.

    Uses AuditableDomainEvent: creating a task is a user-facing action that should
    appear in activity history and trigger real-time updates.
    """

    task_id: UUID
    name: str


@dataclass(frozen=True, kw_only=True)
class TaskStatusChangedEvent(DomainEvent):
    """Event raised when a task's status changes."""

    task_id: UUID
    old_status: str
    new_status: str


@dataclass(frozen=True, kw_only=True)
class TaskPuntedEvent(DomainEvent, AuditableDomainEvent):
    """Event raised when a task is punted.

    Uses AuditableDomainEvent: User explicitly punted a task (postponed it),
    this is a deliberate user choice that represents a significant decision
    in their task management. Important for understanding user behavior patterns.
    """

    task_id: UUID
    old_status: str
    new_status: str
    task_scheduled_date: dt_date | None = None
    task_name: str | None = None
    task_type: str | None = None
    task_category: str | None = None

    def to_audit_log(self, user_id: UUID) -> AuditLogEntity:
        """Create audit log with task-specific entity_data.

        Since this event is raised by the Day aggregate but refers to a Task,
        we need to ensure entity_data contains task information, not day information.
        """
        from lykke.domain.entities.audit_log import AuditLogEntity

        # Build meta with event fields
        meta: dict[str, Any] = {
            "task_id": str(self.task_id),
            "old_status": self.old_status,
            "new_status": self.new_status,
        }

        # Build entity_data with task information
        entity_data: dict[str, Any] = {
            "id": str(self.task_id),
            "user_id": str(user_id),
            "status": self.new_status,
        }

        if self.task_scheduled_date:
            entity_data["scheduled_date"] = self.task_scheduled_date.isoformat()
        if self.task_name:
            entity_data["name"] = self.task_name
        if self.task_type:
            entity_data["type"] = self.task_type
        if self.task_category:
            entity_data["category"] = self.task_category

        meta["entity_data"] = entity_data

        # Extract date from task_scheduled_date if available
        date: dt_date | None = self.task_scheduled_date

        # Use default factory if date is None
        if date is None:
            from lykke.domain.entities.audit_log import _get_user_timezone_date

            date = _get_user_timezone_date()

        return AuditLogEntity(
            user_id=user_id,
            activity_type=self.__class__.__name__,
            entity_id=self.task_id,
            entity_type="task",
            date=date,
            meta=meta,
        )


@dataclass(frozen=True, kw_only=True)
class TaskCompletedEvent(DomainEvent, AuditableDomainEvent):
    """Event raised when a task is completed.

    Uses AuditableDomainEvent: User completed a task - this is a major milestone
    and accomplishment that users want to see in their activity timeline.
    Core to the user experience.
    """

    task_id: UUID
    completed_at: datetime
    task_scheduled_date: dt_date | None = None
    task_name: str | None = None
    task_type: str | None = None
    task_category: str | None = None

    def to_audit_log(self, user_id: UUID) -> AuditLogEntity:
        """Create audit log with task-specific entity_data.

        Since this event is raised by the Day aggregate but refers to a Task,
        we need to ensure entity_data contains task information, not day information.
        """
        from lykke.domain.entities.audit_log import AuditLogEntity

        # Build meta with event fields
        meta: dict[str, Any] = {
            "task_id": str(self.task_id),
            "completed_at": self.completed_at.isoformat(),
        }

        # Build entity_data with task information
        entity_data: dict[str, Any] = {
            "id": str(self.task_id),
            "user_id": str(user_id),
            "status": "COMPLETE",
        }

        if self.task_scheduled_date:
            entity_data["scheduled_date"] = self.task_scheduled_date.isoformat()
        if self.task_name:
            entity_data["name"] = self.task_name
        if self.task_type:
            entity_data["type"] = self.task_type
        if self.task_category:
            entity_data["category"] = self.task_category

        meta["entity_data"] = entity_data

        # Extract date from task_scheduled_date if available
        date: dt_date | None = self.task_scheduled_date

        # Use default factory if date is None
        if date is None:
            from lykke.domain.entities.audit_log import _get_user_timezone_date

            date = _get_user_timezone_date()

        return AuditLogEntity(
            user_id=user_id,
            activity_type=self.__class__.__name__,
            entity_id=self.task_id,
            entity_type="task",
            date=date,
            meta=meta,
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
    completed_at: datetime | None


@dataclass(frozen=True, kw_only=True)
class TaskDefinitionUpdatedEvent(EntityUpdatedEvent[TaskDefinitionUpdateObject]):
    """Event raised when a task definition is updated via apply_update()."""
