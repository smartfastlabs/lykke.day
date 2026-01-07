"""Filtering utilities for calendar entries."""

import datetime

from lykke.domain.entities import CalendarEntryEntity
from lykke.core.utils.dates import get_current_datetime


def is_calendar_entry_eligible_for_upcoming(
    calendar_entry: CalendarEntryEntity,
    now: datetime.datetime,
    look_ahead: datetime.timedelta,
) -> bool:
    """Check if a calendar entry is eligible to be included in upcoming entries.

    Args:
        calendar_entry: The calendar entry to check
        now: Current datetime
        look_ahead: The time window to look ahead

    Returns:
        True if the calendar entry should be included, False otherwise
    """
    # Exclude cancelled calendar entries
    if calendar_entry.status == "cancelled":
        return False

    # Exclude calendar entries that have already ended
    if calendar_entry.ends_at and calendar_entry.ends_at < now:
        return False

    # Include calendar entries that are ongoing (started but not ended)
    if calendar_entry.starts_at <= now:
        return True

    # Exclude calendar entries that are too far in the future
    if (calendar_entry.starts_at - now) > look_ahead:
        return False

    # Calendar entry will start within look_ahead window
    return True


def filter_upcoming_calendar_entries(
    calendar_entries: list[CalendarEntryEntity],
    look_ahead: datetime.timedelta,
) -> list[CalendarEntryEntity]:
    """Filter calendar entries to only include those that are upcoming within the look-ahead window.

    Args:
        calendar_entries: List of calendar entries to filter
        look_ahead: The time window to look ahead

    Returns:
        List of calendar entries that are upcoming within the look-ahead window
    """
    now: datetime.datetime = get_current_datetime()
    result: list[CalendarEntryEntity] = []

    for calendar_entry in calendar_entries:
        if is_calendar_entry_eligible_for_upcoming(calendar_entry, now, look_ahead):
            result.append(calendar_entry)

    return result

