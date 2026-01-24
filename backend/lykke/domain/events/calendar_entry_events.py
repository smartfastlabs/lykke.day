"""Domain events related to CalendarEntry aggregates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from lykke.domain.value_objects.update import CalendarEntryUpdateObject

from .base import DomainEvent, EntityUpdatedEvent

if TYPE_CHECKING:
    from uuid import UUID

__all__ = [
    "CalendarEntryCreatedEvent",
    "CalendarEntryDeletedEvent",
    "CalendarEntryUpdatedEvent",
]


@dataclass(frozen=True, kw_only=True)
class CalendarEntryCreatedEvent(DomainEvent):
    """Event raised when a calendar entry is created."""

    calendar_entry_id: UUID


@dataclass(frozen=True, kw_only=True)
class CalendarEntryUpdatedEvent(EntityUpdatedEvent[CalendarEntryUpdateObject]):
    """Event raised when a calendar entry is updated."""

    calendar_entry_id: UUID


@dataclass(frozen=True, kw_only=True)
class CalendarEntryDeletedEvent(DomainEvent):
    """Event raised when a calendar entry is deleted."""

    calendar_entry_id: UUID
    # Include snapshot of entry data for notification payloads
    entry_snapshot: dict[str, Any]
