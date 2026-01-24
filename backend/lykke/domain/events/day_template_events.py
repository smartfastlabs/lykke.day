"""Domain events related to DayTemplate aggregates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lykke.domain.value_objects.update import DayTemplateUpdateObject

from .base import DomainEvent, EntityUpdatedEvent

if TYPE_CHECKING:
    from datetime import time
    from uuid import UUID


@dataclass(frozen=True, kw_only=True)
class DayTemplateUpdatedEvent(EntityUpdatedEvent[DayTemplateUpdateObject]):
    """Event raised when a day template is updated via apply_update()."""


@dataclass(frozen=True, kw_only=True)
class DayTemplateRoutineDefinitionAddedEvent(DomainEvent):
    """Raised when a routine definition is attached to a day template."""

    day_template_id: UUID
    routine_definition_id: UUID


@dataclass(frozen=True, kw_only=True)
class DayTemplateRoutineDefinitionRemovedEvent(DomainEvent):
    """Raised when a routine definition is detached from a day template."""

    day_template_id: UUID
    routine_definition_id: UUID


@dataclass(frozen=True, kw_only=True)
class DayTemplateTimeBlockAddedEvent(DomainEvent):
    """Raised when a time block is added to a day template."""

    day_template_id: UUID
    time_block_definition_id: UUID
    start_time: time
    end_time: time


@dataclass(frozen=True, kw_only=True)
class DayTemplateTimeBlockRemovedEvent(DomainEvent):
    """Raised when a time block is removed from a day template."""

    day_template_id: UUID
    time_block_definition_id: UUID
    start_time: time
