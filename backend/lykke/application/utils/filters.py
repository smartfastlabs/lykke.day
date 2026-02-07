"""Query filtering utilities for tasks and calendar entries."""

import datetime

from lykke.core.utils.dates import (
    get_current_datetime,
    get_current_datetime_in_timezone,
    get_current_time,
)
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntryEntity, TaskEntity


def calculate_cutoff_time(
    look_ahead: datetime.timedelta,
    *,
    timezone: str | None = None,
) -> datetime.time:
    """Calculate the cutoff time for the look-ahead window.

    Args:
        look_ahead: The time window to look ahead

    Returns:
        The cutoff time in the configured timezone
    """
    cutoff_datetime_utc = get_current_datetime() + look_ahead
    cutoff_datetime_local = cutoff_datetime_utc.astimezone(
        get_current_datetime_in_timezone(timezone).tzinfo
    )
    return cutoff_datetime_local.time()


def filter_upcoming_tasks(
    tasks: list[TaskEntity],
    look_ahead: datetime.timedelta,
    *,
    timezone: str | None = None,
) -> list[TaskEntity]:
    """Filter tasks to only include those that are upcoming within the look-ahead window.

    Args:
        tasks: List of tasks to filter
        look_ahead: The time window to look ahead

    Returns:
        List of tasks that are upcoming within the look-ahead window
    """
    now: datetime.time = get_current_time(timezone)
    cutoff_time = calculate_cutoff_time(look_ahead, timezone=timezone)

    # If cutoff is before now, it means we're looking at tomorrow
    if cutoff_time < now:
        return tasks

    result: list[TaskEntity] = []
    for task in tasks:
        if task.is_eligible_for_upcoming(now, cutoff_time):
            result.append(task)

    return result


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
        # If user has indicated they will not attend, suppress from "upcoming"
        # notification candidates entirely.
        if value_objects.CalendarEntryAttendanceStatus.blocks_notifications(
            calendar_entry.attendance_status
        ):
            continue
        if calendar_entry.is_eligible_for_upcoming(now, look_ahead):
            result.append(calendar_entry)

    return result
