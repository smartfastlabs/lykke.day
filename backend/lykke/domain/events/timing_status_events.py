"""Domain events for timing status changes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lykke.domain.events.base import DomainEvent
from lykke.domain.value_objects import TimingStatus

if TYPE_CHECKING:
    from datetime import date as dt_date, datetime
    from uuid import UUID

__all__ = [
    "RoutineTimingStatusChangedEvent",
    "TaskTimingStatusChangedEvent",
]


@dataclass(frozen=True, kw_only=True)
class TaskTimingStatusChangedEvent(DomainEvent):
    """Event raised when a task's timing status changes."""

    task_id: UUID
    old_timing_status: TimingStatus
    new_timing_status: TimingStatus
    old_next_available_time: datetime | None = None
    new_next_available_time: datetime | None = None
    task_scheduled_date: dt_date | None = None


@dataclass(frozen=True, kw_only=True)
class RoutineTimingStatusChangedEvent(DomainEvent):
    """Event raised when a routine's timing status changes."""

    routine_id: UUID
    old_timing_status: TimingStatus
    new_timing_status: TimingStatus
    old_next_available_time: datetime | None = None
    new_next_available_time: datetime | None = None
    routine_date: dt_date | None = None
