"""Domain events related to Task aggregates."""

from dataclasses import dataclass
from uuid import UUID

from planned.domain.entities.task_definition import TaskDefinitionEntity
from planned.domain.value_objects.update import TaskDefinitionUpdateObject

from .base import DomainEvent, EntityUpdatedEvent

__all__ = [
    "TaskActionRecordedEvent",
    "TaskCompletedEvent",
    "TaskCreatedEvent",
    "TaskDefinitionUpdatedEvent",
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
class TaskCompletedEvent(DomainEvent):
    """Event raised when a task is completed."""

    task_id: UUID
    completed_at: str  # ISO format datetime string


@dataclass(frozen=True, kw_only=True)
class TaskActionRecordedEvent(DomainEvent):
    """Event raised when an action is recorded on a task."""

    task_id: UUID
    action_type: str


@dataclass(frozen=True, kw_only=True)
class TaskDefinitionUpdatedEvent(
    EntityUpdatedEvent[TaskDefinitionUpdateObject, TaskDefinitionEntity]
):
    """Event raised when a task definition is updated via apply_update()."""
