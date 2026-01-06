"""Domain events for Routine aggregate."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from planned.domain.events.base import DomainEvent
from planned.domain.value_objects.routine import RoutineTask


@dataclass(frozen=True, kw_only=True)
class RoutineTaskAddedEvent(DomainEvent):
    """Raised when a task is attached to a routine."""

    routine_id: UUID
    task: RoutineTask


@dataclass(frozen=True, kw_only=True)
class RoutineTaskUpdatedEvent(DomainEvent):
    """Raised when an attached routine task is updated."""

    routine_id: UUID
    task: RoutineTask


@dataclass(frozen=True, kw_only=True)
class RoutineTaskRemovedEvent(DomainEvent):
    """Raised when a task is detached from a routine."""

    routine_id: UUID
    task_definition_id: UUID

