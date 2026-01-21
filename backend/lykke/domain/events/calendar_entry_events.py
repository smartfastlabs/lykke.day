"""Domain events related to CalendarEntry aggregates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from lykke.domain.value_objects.update import CalendarEntryUpdateObject

from .base import DomainEvent, EntityUpdatedEvent

__all__ = [
    "CalendarEntryCreatedEvent",
    "CalendarEntryUpdatedEvent",
    "CalendarEntryDeletedEvent",
]


@dataclass(frozen=True, kw_only=True)
class CalendarEntryCreatedEvent(DomainEvent):
    """Event raised when a calendar entry is created."""

    calendar_entry_id: UUID
    user_id: UUID


@dataclass(frozen=True, kw_only=True)
class CalendarEntryUpdatedEvent(EntityUpdatedEvent[CalendarEntryUpdateObject]):
    """Event raised when a calendar entry is updated."""

    calendar_entry_id: UUID
    user_id: UUID


@dataclass(frozen=True, kw_only=True)
class CalendarEntryDeletedEvent(DomainEvent):
    """Event raised when a calendar entry is deleted."""

    calendar_entry_id: UUID
    user_id: UUID
    # Include snapshot of entry data for notification payloads
    entry_snapshot: dict[str, Any]
