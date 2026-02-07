"""Unit tests for calendar entry filtering utilities."""

import datetime
from datetime import UTC, timedelta
from uuid import uuid4

import pytest
from freezegun import freeze_time

from lykke.application.utils.filters import filter_upcoming_calendar_entries
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntity, CalendarEntryEntity


@pytest.fixture
def test_calendar_entry(test_user_id: str) -> CalendarEntryEntity:
    """Create a calendar entry for testing."""
    calendar = CalendarEntity(
        user_id=test_user_id,
        name="Test Calendar",
        platform="google",
        platform_id="cal123",
        auth_token_id=uuid4(),
    )
    return CalendarEntryEntity(
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
    test_calendar_entry: CalendarEntryEntity,
) -> None:
    """Test cancelled calendar entries are not eligible."""
    test_calendar_entry.status = "cancelled"
    with freeze_time("2025-11-27 10:00:00-06:00", real_asyncio=True):
        now = datetime.datetime(2025, 11, 27, 10, 0, 0, tzinfo=UTC)
        look_ahead = timedelta(hours=3)
        result = test_calendar_entry.is_eligible_for_upcoming(now, look_ahead)
        assert result is False


def test_is_calendar_entry_eligible_for_upcoming_ended(
    test_calendar_entry: CalendarEntryEntity,
) -> None:
    """Test calendar entries that have ended are not eligible."""
    with freeze_time("2025-11-27 14:00:00-06:00", real_asyncio=True):
        now = datetime.datetime(2025, 11, 27, 14, 0, 0, tzinfo=UTC)
        look_ahead = timedelta(hours=3)
        result = test_calendar_entry.is_eligible_for_upcoming(now, look_ahead)
        assert result is False


def test_is_calendar_entry_eligible_for_upcoming_ongoing(
    test_calendar_entry: CalendarEntryEntity,
) -> None:
    """Test ongoing calendar entries are eligible."""
    with freeze_time("2025-11-27 12:30:00-06:00", real_asyncio=True):
        now = datetime.datetime(2025, 11, 27, 12, 30, 0, tzinfo=UTC)
        look_ahead = timedelta(hours=3)
        result = test_calendar_entry.is_eligible_for_upcoming(now, look_ahead)
        assert result is True


def test_is_calendar_entry_eligible_for_upcoming_within_look_ahead(
    test_calendar_entry: CalendarEntryEntity,
) -> None:
    """Test calendar entries starting within look_ahead are eligible."""
    with freeze_time("2025-11-27 10:00:00-06:00", real_asyncio=True):
        now = datetime.datetime(2025, 11, 27, 10, 0, 0, tzinfo=UTC)
        look_ahead = timedelta(hours=3)
        result = test_calendar_entry.is_eligible_for_upcoming(now, look_ahead)
        assert result is True


def test_is_calendar_entry_eligible_for_upcoming_too_far_future(
    test_calendar_entry: CalendarEntryEntity,
) -> None:
    """Test calendar entries too far in future are not eligible."""
    test_calendar_entry.starts_at = datetime.datetime(
        2025, 11, 27, 20, 0, 0, tzinfo=UTC
    )
    test_calendar_entry.ends_at = datetime.datetime(2025, 11, 27, 21, 0, 0, tzinfo=UTC)
    with freeze_time("2025-11-27 10:00:00-06:00", real_asyncio=True):
        now = datetime.datetime(2025, 11, 27, 10, 0, 0, tzinfo=UTC)
        look_ahead = timedelta(hours=3)
        result = test_calendar_entry.is_eligible_for_upcoming(now, look_ahead)
        assert result is False


def test_is_calendar_entry_eligible_for_upcoming_no_ends_at(
    test_user_id: str,
) -> None:
    """Test calendar entries without ends_at are handled correctly."""
    calendar = CalendarEntity(
        user_id=test_user_id,
        name="Test Calendar",
        platform="google",
        platform_id="cal123",
        auth_token_id=uuid4(),
    )
    entry = CalendarEntryEntity(
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
        result = entry.is_eligible_for_upcoming(now, look_ahead)
        assert result is True


def test_filter_upcoming_calendar_entries(test_user_id: str) -> None:
    """Test filter_upcoming_calendar_entries filters entries correctly."""
    auth_token_id = uuid4()
    calendar = CalendarEntity(
        user_id=test_user_id,
        name="Test Calendar",
        platform="google",
        platform_id="cal123",
        auth_token_id=auth_token_id,
    )
    # Eligible entry starts at 12:00 UTC, which is within 3 hours of 10:00 UTC
    eligible_entry = CalendarEntryEntity(
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
    cancelled_entry = CalendarEntryEntity(
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
    future_entry = CalendarEntryEntity(
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

    # Freeze time at 10:00 UTC (not local time) to match get_current_datetime() which returns UTC
    with freeze_time("2025-11-27 10:00:00+00:00", real_asyncio=True):
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


def test_filter_upcoming_calendar_entries_excludes_not_going(test_user_id: str) -> None:
    """Entries marked NOT_GOING should not be included in upcoming results."""
    calendar = CalendarEntity(
        user_id=test_user_id,
        name="Test Calendar",
        platform="google",
        platform_id="cal123",
        auth_token_id=uuid4(),
    )
    not_going_entry = CalendarEntryEntity(
        user_id=test_user_id,
        calendar_id=calendar.id,
        name="Not going event",
        starts_at=datetime.datetime(2025, 11, 27, 12, 0, 0, tzinfo=UTC),
        ends_at=datetime.datetime(2025, 11, 27, 13, 0, 0, tzinfo=UTC),
        platform_id="event-ng",
        platform="google",
        status="confirmed",
        attendance_status=value_objects.CalendarEntryAttendanceStatus.NOT_GOING,
        frequency=value_objects.TaskFrequency.ONCE,
    )

    with freeze_time("2025-11-27 10:00:00+00:00", real_asyncio=True):
        look_ahead = timedelta(hours=3)
        result = filter_upcoming_calendar_entries([not_going_entry], look_ahead)
        assert result == []


def test_filter_upcoming_calendar_entries_ongoing_events(
    test_user_id: str,
) -> None:
    """Test filter_upcoming_calendar_entries includes ongoing events."""
    calendar = CalendarEntity(
        user_id=test_user_id,
        name="Test Calendar",
        platform="google",
        platform_id="cal123",
        auth_token_id=uuid4(),
    )
    ongoing_entry = CalendarEntryEntity(
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

    # Freeze time at 10:00 UTC - event started at 9:00 UTC, so it's ongoing
    with freeze_time("2025-11-27 10:00:00+00:00", real_asyncio=True):
        look_ahead = timedelta(hours=3)
        result = filter_upcoming_calendar_entries([ongoing_entry], look_ahead)
        assert len(result) == 1
        assert result[0].name == "Ongoing Event"
