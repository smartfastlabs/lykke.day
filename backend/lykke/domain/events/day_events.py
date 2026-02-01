"""Domain events related to Day aggregates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from lykke.domain.entities.audit_log import AuditLogEntity
from lykke.domain.value_objects.day import AlarmStatus, AlarmType
from lykke.domain.value_objects.update import DayUpdateObject

from .base import AuditableDomainEvent, DomainEvent, EntityUpdatedEvent

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
class _AlarmDayEventBase(DomainEvent, AuditableDomainEvent):
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

    def to_audit_log(self, user_id: UUID) -> AuditLogEntity:
        """Create audit log with day context for alarm trigger."""
        entity_data: dict[str, Any] = {
            "id": str(self.day_id),
            "date": self.date.isoformat(),
        }

        meta: dict[str, Any] = {
            "day_id": str(self.day_id),
            "date": self.date.isoformat(),
            "alarm_id": str(self.alarm_id),
            "alarm_name": self.alarm_name,
            "alarm_time": self.alarm_time.isoformat(),
            "alarm_type": self.alarm_type.value,
            "alarm_url": self.alarm_url,
            "alarm_status": self.alarm_status.value,
            "entity_data": entity_data,
        }

        return AuditLogEntity(
            user_id=user_id,
            activity_type=self.__class__.__name__,
            entity_id=self.day_id,
            entity_type="day",
            date=self.date,
            meta=meta,
        )


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

    def to_audit_log(self, user_id: UUID) -> AuditLogEntity:
        """Create audit log with day context for alarm status change."""
        entity_data: dict[str, Any] = {
            "id": str(self.day_id),
            "date": self.date.isoformat(),
        }

        meta: dict[str, Any] = {
            "day_id": str(self.day_id),
            "date": self.date.isoformat(),
            "alarm_id": str(self.alarm_id),
            "alarm_name": self.alarm_name,
            "alarm_time": self.alarm_time.isoformat(),
            "alarm_type": self.alarm_type.value,
            "alarm_url": self.alarm_url,
            "old_status": self.old_status.value,
            "new_status": self.new_status.value,
            "entity_data": entity_data,
        }

        return AuditLogEntity(
            user_id=user_id,
            activity_type=self.__class__.__name__,
            entity_id=self.day_id,
            entity_type="day",
            date=self.date,
            meta=meta,
        )


@dataclass(frozen=True, kw_only=True)
class BrainDumpAddedEvent(DomainEvent, AuditableDomainEvent):
    """Event raised when a brain dump is added.

    Uses AuditableDomainEvent: User explicitly added a brain dump,
    this is a user-facing action they'd want to see in their activity timeline.
    """

    day_id: UUID
    date: dt_date
    item_id: UUID
    item_text: str


@dataclass(frozen=True, kw_only=True)
class BrainDumpStatusChangedEvent(DomainEvent, AuditableDomainEvent):
    """Event raised when a brain dump status changes.

    Uses AuditableDomainEvent: User changed status of brain dump
    (e.g., marked as done), this is a user-facing action worth tracking.
    """

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
class BrainDumpRemovedEvent(DomainEvent, AuditableDomainEvent):
    """Event raised when a brain dump is removed.

    Uses AuditableDomainEvent: User explicitly removed a brain dump,
    this is a user-facing action they'd want to see in their history.
    """

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
