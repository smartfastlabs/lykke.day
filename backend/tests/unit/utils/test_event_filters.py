"""Unit tests for calendar entry filtering utilities."""

import datetime
from datetime import UTC, timedelta

import pytest
from freezegun import freeze_time

from planned.application.utils.event_filters import (
    filter_upcoming_calendar_entries,
    is_calendar_entry_eligible_for_upcoming,
)
from planned.domain import entities, value_objects


@pytest.fixture
def test_calendar_entry(test_user_id: str) -> entities.CalendarEntry:
    """Create a calendar entry for testing."""
    from uuid import uuid4
    
    calendar = entities.Calendar(
        user_id=test_user_id,
        name="Test Calendar",
        platform="google",
        platform_id="cal123",
        auth_token_id=uuid4(),
    )
    return entities.CalendarEntry(
        user_id=test_user_id,
        calendar_id=calendar.id,
        name="Test Event",
        starts_at=datetime.datetime(2025, 11, 27, 12, 0, 0, tzinfo=UTC),
        ends_at=datetime.datetime(2025, 11, 27, 13, 0, 0, tzinfo=UTC),
        platform_id="event123",
        platform="google",
        status="confirmed",
        frequency=value_objects.TaskFrequency.ONCE,
    )


def test_is_calendar_entry_eligible_for_upcoming_cancelled(
    test_calendar_entry: entities.CalendarEntry,
) -> None:
    """Test cancelled calendar entries are not eligible."""
    test_calendar_entry.status = "cancelled"
    with freeze_time("2025-11-27 10:00:00-06:00", real_asyncio=True):
        now = datetime.datetime(2025, 11, 27, 10, 0, 0, tzinfo=UTC)
        look_ahead = timedelta(hours=3)
        result = is_calendar_entry_eligible_for_upcoming(
            test_calendar_entry, now, look_ahead
        )
        assert result is False


def test_is_calendar_entry_eligible_for_upcoming_ended(
    test_calendar_entry: entities.CalendarEntry,
) -> None:
    """Test calendar entries that have ended are not eligible."""
    with freeze_time("2025-11-27 14:00:00-06:00", real_asyncio=True):
        now = datetime.datetime(2025, 11, 27, 14, 0, 0, tzinfo=UTC)
        look_ahead = timedelta(hours=3)
        result = is_calendar_entry_eligible_for_upcoming(
            test_calendar_entry, now, look_ahead
        )
        assert result is False


def test_is_calendar_entry_eligible_for_upcoming_ongoing(
    test_calendar_entry: entities.CalendarEntry,
) -> None:
    """Test ongoing calendar entries are eligible."""
    with freeze_time("2025-11-27 12:30:00-06:00", real_asyncio=True):
        now = datetime.datetime(2025, 11, 27, 12, 30, 0, tzinfo=UTC)
        look_ahead = timedelta(hours=3)
        result = is_calendar_entry_eligible_for_upcoming(
            test_calendar_entry, now, look_ahead
        )
        assert result is True


def test_is_calendar_entry_eligible_for_upcoming_within_look_ahead(
    test_calendar_entry: entities.CalendarEntry,
) -> None:
    """Test calendar entries starting within look_ahead are eligible."""
    with freeze_time("2025-11-27 10:00:00-06:00", real_asyncio=True):
        now = datetime.datetime(2025, 11, 27, 10, 0, 0, tzinfo=UTC)
        look_ahead = timedelta(hours=3)
        result = is_calendar_entry_eligible_for_upcoming(
            test_calendar_entry, now, look_ahead
        )
        assert result is True


def test_is_calendar_entry_eligible_for_upcoming_too_far_future(
    test_calendar_entry: entities.CalendarEntry,
) -> None:
    """Test calendar entries too far in future are not eligible."""
    test_calendar_entry.starts_at = datetime.datetime(
        2025, 11, 27, 20, 0, 0, tzinfo=UTC
    )
    test_calendar_entry.ends_at = datetime.datetime(
        2025, 11, 27, 21, 0, 0, tzinfo=UTC
    )
    with freeze_time("2025-11-27 10:00:00-06:00", real_asyncio=True):
        now = datetime.datetime(2025, 11, 27, 10, 0, 0, tzinfo=UTC)
        look_ahead = timedelta(hours=3)
        result = is_calendar_entry_eligible_for_upcoming(
            test_calendar_entry, now, look_ahead
        )
        assert result is False


def test_is_calendar_entry_eligible_for_upcoming_no_ends_at(
    test_user_id: str,
) -> None:
    """Test calendar entries without ends_at are handled correctly."""
    from uuid import uuid4
    
    calendar = entities.Calendar(
        user_id=test_user_id,
        name="Test Calendar",
        platform="google",
        platform_id="cal123",
        auth_token_id=uuid4(),
    )
    entry = entities.CalendarEntry(
        user_id=test_user_id,
        calendar_id=calendar.id,
        name="All Day Event",
        starts_at=datetime.datetime(2025, 11, 27, 12, 0, 0, tzinfo=UTC),
        ends_at=None,
        platform_id="event123",
        platform="google",
        status="confirmed",
        frequency=value_objects.TaskFrequency.ONCE,
    )
    with freeze_time("2025-11-27 10:00:00-06:00", real_asyncio=True):
        now = datetime.datetime(2025, 11, 27, 10, 0, 0, tzinfo=UTC)
        look_ahead = timedelta(hours=3)
        result = is_calendar_entry_eligible_for_upcoming(entry, now, look_ahead)
        assert result is True


def test_filter_upcoming_calendar_entries(test_user_id: str) -> None:
    """Test filter_upcoming_calendar_entries filters entries correctly."""
    from uuid import uuid4
    
    auth_token_id = uuid4()
    calendar = entities.Calendar(
        user_id=test_user_id,
        name="Test Calendar",
        platform="google",
        platform_id="cal123",
        auth_token_id=auth_token_id,
    )
    eligible_entry = entities.CalendarEntry(
        user_id=test_user_id,
        calendar_id=calendar.id,
        name="Eligible Event",
        starts_at=datetime.datetime(2025, 11, 27, 12, 0, 0, tzinfo=UTC),
        ends_at=datetime.datetime(2025, 11, 27, 13, 0, 0, tzinfo=UTC),
        platform_id="event1",
        platform="google",
        status="confirmed",
        frequency=value_objects.TaskFrequency.ONCE,
    )
    cancelled_entry = entities.CalendarEntry(
        user_id=test_user_id,
        calendar_id=calendar.id,
        name="Cancelled Event",
        starts_at=datetime.datetime(2025, 11, 27, 12, 0, 0, tzinfo=UTC),
        ends_at=datetime.datetime(2025, 11, 27, 13, 0, 0, tzinfo=UTC),
        platform_id="event2",
        platform="google",
        status="cancelled",
        frequency=value_objects.TaskFrequency.ONCE,
    )
    future_entry = entities.CalendarEntry(
        user_id=test_user_id,
        calendar_id=calendar.id,
        name="Future Event",
        starts_at=datetime.datetime(2025, 11, 27, 20, 0, 0, tzinfo=UTC),
        ends_at=datetime.datetime(2025, 11, 27, 21, 0, 0, tzinfo=UTC),
        platform_id="event3",
        platform="google",
        status="confirmed",
        frequency=value_objects.TaskFrequency.ONCE,
    )

    entries = [eligible_entry, cancelled_entry, future_entry]

    with freeze_time("2025-11-27 10:00:00-06:00", real_asyncio=True):
        look_ahead = timedelta(hours=3)
        result = filter_upcoming_calendar_entries(entries, look_ahead)
        assert len(result) == 1
        assert result[0].name == "Eligible Event"


def test_filter_upcoming_calendar_entries_empty_list() -> None:
    """Test filter_upcoming_calendar_entries handles empty list."""
    with freeze_time("2025-11-27 10:00:00-06:00", real_asyncio=True):
        look_ahead = timedelta(hours=3)
        result = filter_upcoming_calendar_entries([], look_ahead)
        assert result == []


def test_filter_upcoming_calendar_entries_ongoing_events(
    test_user_id: str,
) -> None:
    """Test filter_upcoming_calendar_entries includes ongoing events."""
    from uuid import uuid4
    
    calendar = entities.Calendar(
        user_id=test_user_id,
        name="Test Calendar",
        platform="google",
        platform_id="cal123",
        auth_token_id=uuid4(),
    )
    ongoing_entry = entities.CalendarEntry(
        user_id=test_user_id,
        calendar_id=calendar.id,
        name="Ongoing Event",
        starts_at=datetime.datetime(2025, 11, 27, 9, 0, 0, tzinfo=UTC),
        ends_at=datetime.datetime(2025, 11, 27, 13, 0, 0, tzinfo=UTC),
        platform_id="event123",
        platform="google",
        status="confirmed",
        frequency=value_objects.TaskFrequency.ONCE,
    )

    with freeze_time("2025-11-27 10:00:00-06:00", real_asyncio=True):
        look_ahead = timedelta(hours=3)
        result = filter_upcoming_calendar_entries([ongoing_entry], look_ahead)
        assert len(result) == 1
        assert result[0].name == "Ongoing Event"

