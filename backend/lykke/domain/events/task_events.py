"""Domain events related to Task aggregates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lykke.domain.value_objects.update import (
    TaskDefinitionUpdateObject,
    TaskUpdateObject,
)

from .base import DomainEvent, EntityUpdatedEvent

if TYPE_CHECKING:
    from datetime import date as dt_date, datetime
    from uuid import UUID

__all__ = [
    "TaskActionRecordedEvent",
    "TaskCompletedEvent",
    "TaskCreatedEvent",
    "TaskDefinitionUpdatedEvent",
    "TaskPuntedEvent",
    "TaskStateUpdatedEvent",
    "TaskStatusChangedEvent",
    "TaskUpdatedEvent",
]


@dataclass(frozen=True, kw_only=True)
class TaskCreatedEvent(DomainEvent):
    """Event raised when a task is created."""

    task_id: UUID
    name: str


@dataclass(frozen=True, kw_only=True)
class TaskStatusChangedEvent(DomainEvent):
    """Event raised when a task's status changes."""

    task_id: UUID
    old_status: str
    new_status: str


@dataclass(frozen=True, kw_only=True)
class TaskPuntedEvent(DomainEvent):
    """Event raised when a task is punted."""

    task_id: UUID
    old_status: str
    new_status: str
    task_scheduled_date: dt_date | None = None
    task_name: str | None = None
    task_type: str | None = None
    task_category: str | None = None

@dataclass(frozen=True, kw_only=True)
class TaskCompletedEvent(DomainEvent):
    """Event raised when a task is completed."""

    task_id: UUID
    completed_at: datetime
    task_scheduled_date: dt_date | None = None
    task_name: str | None = None
    task_type: str | None = None
    task_category: str | None = None

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


@dataclass(frozen=True, kw_only=True)
class TaskUpdatedEvent(EntityUpdatedEvent[TaskUpdateObject]):
    """Event raised when a task is updated via apply_update()."""
