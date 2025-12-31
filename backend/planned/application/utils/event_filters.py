"""Filtering utilities for events."""

import datetime

from planned.domain import entities as objects
from planned.infrastructure.utils.dates import get_current_datetime


def is_event_eligible_for_upcoming(
    event: objects.Event,
    now: datetime.datetime,
    look_ahead: datetime.timedelta,
) -> bool:
    """Check if an event is eligible to be included in upcoming events.

    Args:
        event: The event to check
        now: Current datetime
        look_ahead: The time window to look ahead

    Returns:
        True if the event should be included, False otherwise
    """
    # Exclude cancelled events
    if event.status == "cancelled":
        return False

    # Exclude events that have already ended
    if event.ends_at and event.ends_at < now:
        return False

    # Include events that are ongoing (started but not ended)
    if event.starts_at <= now:
        return True

    # Exclude events that are too far in the future
    if (event.starts_at - now) > look_ahead:
        return False

    # Event will start within look_ahead window
    return True


def filter_upcoming_events(
    events: list[objects.Event],
    look_ahead: datetime.timedelta,
) -> list[objects.Event]:
    """Filter events to only include those that are upcoming within the look-ahead window.

    Args:
        events: List of events to filter
        look_ahead: The time window to look ahead

    Returns:
        List of events that are upcoming within the look-ahead window
    """
    now: datetime.datetime = get_current_datetime()
    result: list[objects.Event] = []

    for event in events:
        if is_event_eligible_for_upcoming(event, now, look_ahead):
            result.append(event)

    return result

