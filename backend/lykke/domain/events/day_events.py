"""Domain events related to Day aggregates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from lykke.domain.value_objects.day import AlarmStatus, AlarmType
from lykke.domain.value_objects.update import DayUpdateObject

from .base import DomainEvent, EntityUpdatedEvent

if TYPE_CHECKING:
    from datetime import date as dt_date, time
    from uuid import UUID

    from lykke.domain.value_objects.day import BrainDumpStatus, BrainDumpType


@dataclass(frozen=True, kw_only=True)
class DayScheduledEvent(DomainEvent):
    """Event raised when a day is scheduled."""

    day_id: UUID
    date: dt_date
    template_id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class NewDayEvent(DomainEvent):
    """Event raised when a new day is created and scheduled."""

    day_id: UUID
    date: dt_date


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


@dataclass(frozen=True, kw_only=True)
class DayUpdatedEvent(EntityUpdatedEvent[DayUpdateObject]):
    """Event raised when a day is updated via apply_update()."""


@dataclass(frozen=True, kw_only=True)
class _AlarmDayEventBase(DomainEvent):
    """Base class for alarm events tied to a day."""

    day_id: UUID
    date: dt_date

    def __post_init__(self) -> None:
        if self.entity_id is None:
            object.__setattr__(self, "entity_id", self.day_id)
        if self.entity_type is None:
            object.__setattr__(self, "entity_type", "day")
        if self.entity_date is None:
            object.__setattr__(self, "entity_date", self.date)


@dataclass(frozen=True, kw_only=True)
class AlarmAddedEvent(_AlarmDayEventBase):
    """Event raised when an alarm is added to a day."""

    alarm_name: str
    alarm_time: time
    alarm_type: AlarmType
    alarm_url: str


@dataclass(frozen=True, kw_only=True)
class AlarmRemovedEvent(_AlarmDayEventBase):
    """Event raised when an alarm is removed from a day."""

    alarm_name: str
    alarm_time: time
    alarm_type: AlarmType
    alarm_url: str


@dataclass(frozen=True, kw_only=True)
class AlarmTriggeredEvent(_AlarmDayEventBase):
    """Event raised when an alarm is triggered."""

    alarm_id: UUID
    alarm_name: str
    alarm_time: time
    alarm_type: AlarmType
    alarm_url: str
    alarm_status: AlarmStatus = AlarmStatus.TRIGGERED


@dataclass(frozen=True, kw_only=True)
class AlarmStatusChangedEvent(_AlarmDayEventBase):
    """Event raised when an alarm's status changes."""

    alarm_id: UUID
    alarm_name: str
    alarm_time: time
    alarm_type: AlarmType
    alarm_url: str
    old_status: AlarmStatus
    new_status: AlarmStatus


@dataclass(frozen=True, kw_only=True)
class BrainDumpAddedEvent(DomainEvent):
    """Event raised when a brain dump is added."""

    day_id: UUID
    date: dt_date
    item_id: UUID
    item_text: str


@dataclass(frozen=True, kw_only=True)
class BrainDumpStatusChangedEvent(DomainEvent):
    """Event raised when a brain dump status changes."""

    day_id: UUID
    date: dt_date
    item_id: UUID
    old_status: BrainDumpStatus
    new_status: BrainDumpStatus
    item_text: str


@dataclass(frozen=True, kw_only=True)
class BrainDumpTypeChangedEvent(DomainEvent):
    """Event raised when a brain dump's type changes."""

    day_id: UUID
    date: dt_date
    item_id: UUID
    old_type: BrainDumpType
    new_type: BrainDumpType
    item_text: str


@dataclass(frozen=True, kw_only=True)
class BrainDumpLLMRunRecordedEvent(DomainEvent):
    """Event raised when an LLM run result is stored for a brain dump."""

    user_id: UUID
    day_id: UUID
    date: dt_date
    item_id: UUID


@dataclass(frozen=True, kw_only=True)
class BrainDumpRemovedEvent(DomainEvent):
    """Event raised when a brain dump is removed."""

    day_id: UUID
    date: dt_date
    item_id: UUID
    item_text: str


__all__ = [
    "AlarmAddedEvent",
    "AlarmRemovedEvent",
    "AlarmStatusChangedEvent",
    "AlarmTriggeredEvent",
    "BrainDumpAddedEvent",
    "BrainDumpLLMRunRecordedEvent",
    "BrainDumpRemovedEvent",
    "BrainDumpStatusChangedEvent",
    "BrainDumpTypeChangedEvent",
    "DayCompletedEvent",
    "DayScheduledEvent",
    "DayUnscheduledEvent",
    "DayUpdatedEvent",
    "NewDayEvent",
]
