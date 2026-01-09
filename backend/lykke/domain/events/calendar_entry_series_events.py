"""Domain events for CalendarEntrySeries aggregates."""

from __future__ import annotations

from dataclasses import dataclass

from lykke.domain.value_objects.update import CalendarEntrySeriesUpdateObject

from .base import EntityUpdatedEvent


@dataclass(frozen=True, kw_only=True)
class CalendarEntrySeriesUpdatedEvent(
    EntityUpdatedEvent[CalendarEntrySeriesUpdateObject]
):
    """Event raised when a calendar entry series is updated."""


