"""Domain events related to Calendar aggregates."""

from __future__ import annotations

from dataclasses import dataclass

from lykke.domain.value_objects.update import CalendarUpdateObject

from .base import DomainEvent, EntityUpdatedEvent


@dataclass(frozen=True, kw_only=True)
class CalendarUpdatedEvent(EntityUpdatedEvent[CalendarUpdateObject]):
    """Event raised when a calendar is updated via apply_update()."""

