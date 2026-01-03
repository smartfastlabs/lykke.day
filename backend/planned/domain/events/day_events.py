"""Domain events related to Day aggregates."""

from dataclasses import dataclass
from datetime import date as dt_date
from uuid import UUID

from .base import DomainEvent


@dataclass(frozen=True, kw_only=True)
class DayScheduledEvent(DomainEvent):
    """Event raised when a day is scheduled."""

    day_id: UUID
    date: dt_date
    template_id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class DayCompletedEvent(DomainEvent):
    """Event raised when a day is marked as complete."""

    day_id: UUID
    date: dt_date


@dataclass(frozen=True, kw_only=True)
class DayUnscheduledEvent(DomainEvent):
    """Event raised when a day is unscheduled."""

    day_id: UUID
    date: dt_date
