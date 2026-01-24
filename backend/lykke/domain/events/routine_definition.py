"""Domain events for RoutineDefinition aggregate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lykke.domain.events.base import DomainEvent, EntityUpdatedEvent
from lykke.domain.value_objects.update import RoutineDefinitionUpdateObject

if TYPE_CHECKING:
    from uuid import UUID

    from lykke.domain.value_objects.routine_definition import RoutineDefinitionTask


@dataclass(frozen=True, kw_only=True)
class RoutineDefinitionTaskAddedEvent(DomainEvent):
    """Raised when a task is attached to a routine definition."""

    routine_definition_id: UUID
    task: RoutineDefinitionTask


@dataclass(frozen=True, kw_only=True)
class RoutineDefinitionTaskUpdatedEvent(DomainEvent):
    """Raised when an attached routine definition task is updated."""

    routine_definition_id: UUID
    task: RoutineDefinitionTask


@dataclass(frozen=True, kw_only=True)
class RoutineDefinitionTaskRemovedEvent(DomainEvent):
    """Raised when a task is detached from a routine definition."""

    routine_definition_id: UUID
    routine_definition_task_id: UUID  # RoutineDefinitionTask.id
    task_definition_id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class RoutineDefinitionUpdatedEvent(
    EntityUpdatedEvent[RoutineDefinitionUpdateObject]
):
    """Event raised when a routine definition is updated via apply_update()."""
