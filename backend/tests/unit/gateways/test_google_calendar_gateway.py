"""Unit tests for Google Calendar gateway helpers."""

# pylint: disable=protected-access

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from freezegun import freeze_time

from lykke.domain.entities import CalendarEntity
from lykke.domain.value_objects import TaskFrequency
from lykke.infrastructure.gateways.google import GoogleCalendarGateway


def test_parse_event_timestamp_valid_z() -> None:
    """Parses ISO timestamps with Z suffix into UTC."""
    result = GoogleCalendarGateway._parse_event_timestamp(
        "2026-02-02T08:15:37.614Z"
    )

    assert result == datetime(2026, 2, 2, 8, 15, 37, 614000, tzinfo=UTC)


def test_parse_event_timestamp_naive_assumes_utc() -> None:
    """Naive timestamps are treated as UTC."""
    result = GoogleCalendarGateway._parse_event_timestamp(
        "2026-02-02T08:15:37.614"
    )

    assert result == datetime(2026, 2, 2, 8, 15, 37, 614000, tzinfo=UTC)


def test_parse_event_timestamp_invalid_year_falls_back() -> None:
    """Invalid years fall back to the current UTC time."""
    with freeze_time("2026-02-02 09:00:00+00:00", real_asyncio=True):
        result = GoogleCalendarGateway._parse_event_timestamp(
            "0000-12-31T00:00:00.000Z"
        )

    assert result == datetime(2026, 2, 2, 9, 0, 0, tzinfo=UTC)


def test_parse_event_timestamp_non_string_falls_back() -> None:
    """Non-string values fall back to the current UTC time."""
    with freeze_time("2026-02-02 09:30:00+00:00", real_asyncio=True):
        result = GoogleCalendarGateway._parse_event_timestamp(None)

    assert result == datetime(2026, 2, 2, 9, 30, 0, tzinfo=UTC)


def test_google_event_to_entity_derives_recurring_event_id() -> None:
    """Derives recurring id from instance event ids."""
    calendar = CalendarEntity(
        id=uuid4(),
        user_id=uuid4(),
        name="Test Calendar",
        auth_token_id=uuid4(),
        platform_id="test@calendar.google.com",
        platform="google",
    )
    event = {
        "id": "series123_20260204T081500Z",
        "summary": "Recurring Event",
        "status": "confirmed",
        "start": {"dateTime": "2026-02-04T08:15:00Z"},
        "end": {"dateTime": "2026-02-04T08:45:00Z"},
        "created": "2026-02-02T08:15:37.614Z",
        "updated": "2026-02-02T08:15:37.614Z",
    }

    recurrence_lookup = SimpleNamespace(
        events=lambda: SimpleNamespace(
            get=lambda **_: SimpleNamespace(
                execute=lambda: {"recurrence": ["RRULE:FREQ=DAILY"]}
            )
        )
    )

    gateway = GoogleCalendarGateway()
    entry, series = gateway._google_event_to_entity(
        calendar=calendar,
        event=event,
        frequency_cache={},
        recurrence_lookup=recurrence_lookup,
        user_timezone="UTC",
    )

    assert series is not None
    assert series.platform_id == "series123"
    assert entry.calendar_entry_series_id == series.id
    assert entry.frequency == TaskFrequency.DAILY


def test_google_event_to_entity_uses_ical_uid_for_recurrence() -> None:
    """Falls back to iCalUID when recurring metadata is incomplete."""
    calendar = CalendarEntity(
        id=uuid4(),
        user_id=uuid4(),
        name="Test Calendar",
        auth_token_id=uuid4(),
        platform_id="test@calendar.google.com",
        platform="google",
    )
    event = {
        "id": "instance-abc123",
        "iCalUID": "series-ical-uid@google.com",
        "summary": "Recurring Event",
        "status": "confirmed",
        "originalStartTime": {"dateTime": "2026-02-04T08:15:00Z"},
        "start": {"dateTime": "2026-02-04T08:15:00Z"},
        "end": {"dateTime": "2026-02-04T08:45:00Z"},
        "created": "2026-02-02T08:15:37.614Z",
        "updated": "2026-02-02T08:15:37.614Z",
    }

    recurrence_lookup = SimpleNamespace(
        events=lambda: SimpleNamespace(
            get=lambda **_: SimpleNamespace(
                execute=lambda: {"recurrence": ["RRULE:FREQ=DAILY"]}
            )
        )
    )

    gateway = GoogleCalendarGateway()
    entry, series = gateway._google_event_to_entity(
        calendar=calendar,
        event=event,
        frequency_cache={},
        recurrence_lookup=recurrence_lookup,
        user_timezone="UTC",
    )

    assert series is not None
    assert series.platform_id == "series-ical-uid@google.com"
    assert entry.calendar_entry_series_id == series.id


def test_google_event_to_entity_normalizes_empty_summary() -> None:
    """Empty summaries should fall back to a placeholder name."""
    calendar = CalendarEntity(
        id=uuid4(),
        user_id=uuid4(),
        name="Test Calendar",
        auth_token_id=uuid4(),
        platform_id="test@calendar.google.com",
        platform="google",
    )
    event = {
        "id": "event-no-title",
        "summary": "   ",
        "status": "confirmed",
        "start": {"dateTime": "2026-02-04T08:15:00Z"},
        "end": {"dateTime": "2026-02-04T08:45:00Z"},
        "created": "2026-02-02T08:15:37.614Z",
        "updated": "2026-02-02T08:15:37.614Z",
    }

    recurrence_lookup = SimpleNamespace(
        events=lambda: SimpleNamespace(
            get=lambda **_: SimpleNamespace(execute=lambda: {"recurrence": None})
        )
    )

    gateway = GoogleCalendarGateway()
    entry, series = gateway._google_event_to_entity(
        calendar=calendar,
        event=event,
        frequency_cache={},
        recurrence_lookup=recurrence_lookup,
        user_timezone="UTC",
    )

    assert series is None
    assert entry.name == "(no title)"


def test_google_event_to_entity_normalizes_missing_summary() -> None:
    """Missing summaries should fall back to a placeholder name."""
    calendar = CalendarEntity(
        id=uuid4(),
        user_id=uuid4(),
        name="Test Calendar",
        auth_token_id=uuid4(),
        platform_id="test@calendar.google.com",
        platform="google",
    )
    event = {
        "id": "event-missing-title",
        "summary": None,
        "status": "confirmed",
        "start": {"dateTime": "2026-02-04T08:15:00Z"},
        "end": {"dateTime": "2026-02-04T08:45:00Z"},
        "created": "2026-02-02T08:15:37.614Z",
        "updated": "2026-02-02T08:15:37.614Z",
    }

    recurrence_lookup = SimpleNamespace(
        events=lambda: SimpleNamespace(
            get=lambda **_: SimpleNamespace(execute=lambda: {"recurrence": None})
        )
    )

    gateway = GoogleCalendarGateway()
    entry, series = gateway._google_event_to_entity(
        calendar=calendar,
        event=event,
        frequency_cache={},
        recurrence_lookup=recurrence_lookup,
        user_timezone="UTC",
    )

    assert series is None
    assert entry.name == "(no title)"
