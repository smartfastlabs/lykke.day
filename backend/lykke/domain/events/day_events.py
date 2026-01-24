"""Domain events related to Day aggregates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lykke.domain.value_objects.update import DayUpdateObject

from .base import AuditableDomainEvent, DomainEvent, EntityUpdatedEvent

if TYPE_CHECKING:
    from datetime import date as dt_date
    from uuid import UUID

    from lykke.domain.value_objects.day import (
        BrainDumpItemStatus,
        BrainDumpItemType,
        ReminderStatus,
    )


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


@dataclass(frozen=True, kw_only=True)
class DayUpdatedEvent(EntityUpdatedEvent[DayUpdateObject]):
    """Event raised when a day is updated via apply_update()."""


@dataclass(frozen=True, kw_only=True)
class ReminderAddedEvent(DomainEvent):
    """Event raised when a reminder is added to a day."""

    day_id: UUID
    date: dt_date
    reminder_id: UUID
    reminder_name: str


@dataclass(frozen=True, kw_only=True)
class ReminderStatusChangedEvent(DomainEvent):
    """Event raised when a reminder status changes."""

    day_id: UUID
    date: dt_date
    reminder_id: UUID
    old_status: ReminderStatus
    new_status: ReminderStatus
    reminder_name: str


@dataclass(frozen=True, kw_only=True)
class ReminderRemovedEvent(DomainEvent):
    """Event raised when a reminder is removed from a day."""

    day_id: UUID
    date: dt_date
    reminder_id: UUID
    reminder_name: str


@dataclass(frozen=True, kw_only=True)
class BrainDumpItemAddedEvent(DomainEvent, AuditableDomainEvent):
    """Event raised when a brain dump item is added.

    Uses AuditableDomainEvent: User explicitly added a brain dump item,
    this is a user-facing action they'd want to see in their activity timeline.
    """

    day_id: UUID
    date: dt_date
    item_id: UUID
    item_text: str


@dataclass(frozen=True, kw_only=True)
class BrainDumpItemStatusChangedEvent(DomainEvent, AuditableDomainEvent):
    """Event raised when a brain dump item status changes.

    Uses AuditableDomainEvent: User changed status of brain dump item
    (e.g., marked as done), this is a user-facing action worth tracking.
    """

    day_id: UUID
    date: dt_date
    item_id: UUID
    old_status: BrainDumpItemStatus
    new_status: BrainDumpItemStatus
    item_text: str


@dataclass(frozen=True, kw_only=True)
class BrainDumpItemTypeChangedEvent(DomainEvent):
    """Event raised when a brain dump item's type changes."""

    day_id: UUID
    date: dt_date
    item_id: UUID
    old_type: BrainDumpItemType
    new_type: BrainDumpItemType
    item_text: str


@dataclass(frozen=True, kw_only=True)
class BrainDumpItemRemovedEvent(DomainEvent, AuditableDomainEvent):
    """Event raised when a brain dump item is removed.

    Uses AuditableDomainEvent: User explicitly removed a brain dump item,
    this is a user-facing action they'd want to see in their history.
    """

    day_id: UUID
    date: dt_date
    item_id: UUID
    item_text: str


__all__ = [
    "BrainDumpItemAddedEvent",
    "BrainDumpItemRemovedEvent",
    "BrainDumpItemStatusChangedEvent",
    "BrainDumpItemTypeChangedEvent",
    "DayCompletedEvent",
    "DayScheduledEvent",
    "DayUnscheduledEvent",
    "DayUpdatedEvent",
    "ReminderAddedEvent",
    "ReminderRemovedEvent",
    "ReminderStatusChangedEvent",
]
