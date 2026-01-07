"""Domain events related to DayTemplate aggregates."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from lykke.domain.value_objects.update import DayTemplateUpdateObject

from .base import DomainEvent, EntityUpdatedEvent


@dataclass(frozen=True, kw_only=True)
class DayTemplateUpdatedEvent(EntityUpdatedEvent[DayTemplateUpdateObject]):
    """Event raised when a day template is updated via apply_update()."""


@dataclass(frozen=True, kw_only=True)
class DayTemplateRoutineAddedEvent(DomainEvent):
    """Raised when a routine is attached to a day template."""

    day_template_id: UUID
    routine_id: UUID


@dataclass(frozen=True, kw_only=True)
class DayTemplateRoutineRemovedEvent(DomainEvent):
    """Raised when a routine is detached from a day template."""

    day_template_id: UUID
    routine_id: UUID

