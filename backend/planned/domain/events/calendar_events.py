"""Domain events related to Calendar aggregates."""

from dataclasses import dataclass

from planned.domain.entities.calendar import CalendarEntity
from planned.domain.value_objects.update import CalendarUpdateObject

from .base import DomainEvent, EntityUpdatedEvent


@dataclass(frozen=True, kw_only=True)
class CalendarUpdatedEvent(EntityUpdatedEvent[CalendarUpdateObject, CalendarEntity]):
    """Event raised when a calendar is updated via apply_update()."""

    pass

