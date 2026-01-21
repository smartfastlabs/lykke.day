"""Domain events for Routine aggregate."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from lykke.domain.events.base import DomainEvent, EntityUpdatedEvent
from lykke.domain.value_objects.routine import RoutineTask
from lykke.domain.value_objects.update import RoutineUpdateObject


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
    routine_task_id: UUID  # RoutineTask.id
    task_definition_id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class RoutineUpdatedEvent(EntityUpdatedEvent[RoutineUpdateObject]):
    """Event raised when a routine is updated via apply_update()."""
