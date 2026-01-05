"""Domain events related to Calendar aggregates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from planned.domain.value_objects.update import CalendarUpdateObject

from .base import DomainEvent, EntityUpdatedEvent

if TYPE_CHECKING:
    from planned.domain.entities.calendar import CalendarEntity


@dataclass(frozen=True, kw_only=True)
class CalendarUpdatedEvent(EntityUpdatedEvent[CalendarUpdateObject, "CalendarEntity"]):
    """Event raised when a calendar is updated via apply_update()."""

