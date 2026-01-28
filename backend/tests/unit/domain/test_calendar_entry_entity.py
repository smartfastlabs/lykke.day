from datetime import UTC, date as dt_date, datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from dateutil.tz import tzoffset

from lykke.domain.value_objects import EventCategory, TaskFrequency
from lykke.infrastructure.mappers import GoogleCalendarMapper, get_datetime

TARGET_TIMEZONE = "America/Chicago"


def test_get_datetime():
    google_dt = datetime(2025, 12, 9, 10, 30, tzinfo=tzoffset(None, -21600))
    google_tz = "America/New_York"

    assert get_datetime(
        google_dt,
        google_tz,
        TARGET_TIMEZONE,
    ) == datetime(2025, 12, 9, 10, 30).replace(tzinfo=ZoneInfo("America/Chicago"))


def test_get_datetime_with_aware_datetime():
    """Datetime with tzinfo should convert to target timezone."""
    google_dt = datetime(2025, 12, 9, 10, 30, tzinfo=tzoffset(None, -21600))
    google_tz = "America/New_York"
    assert get_datetime(google_dt, google_tz, TARGET_TIMEZONE) == datetime(
        2025, 12, 9, 10, 30, tzinfo=ZoneInfo("America/Chicago")
    )


def test_get_datetime_with_aware_datetime_different_offset():
    """Datetime in UTC should convert correctly to Chicago."""
    # 16:30 UTC = 10:30 Chicago (UTC-6 in winter)
    utc_dt = datetime(2025, 12, 9, 16, 30, tzinfo=ZoneInfo("UTC"))
    assert get_datetime(utc_dt, "UTC", TARGET_TIMEZONE) == datetime(
        2025, 12, 9, 10, 30, tzinfo=ZoneInfo("America/Chicago")
    )


def test_get_datetime_with_naive_datetime():
    """Naive datetime should use provided timezone, then convert."""
    # 11:30 in New York = 10:30 in Chicago (both UTC-5 and UTC-6 in winter)
    naive_dt = datetime(2025, 12, 9, 11, 30)
    result = get_datetime(naive_dt, "America/New_York", TARGET_TIMEZONE)
    assert result == datetime(2025, 12, 9, 10, 30, tzinfo=ZoneInfo("America/Chicago"))


def test_get_datetime_with_date_start_of_day():
    """Date should become midnight in target timezone."""
    d = dt_date(2025, 12, 9)
    result = get_datetime(d, "America/New_York", TARGET_TIMEZONE, use_start_of_day=True)
    assert result == datetime(2025, 12, 9, 0, 0, 0, tzinfo=ZoneInfo("America/Chicago"))


def test_get_datetime_with_date_end_of_day():
    """Date should become 23:59:59 in target timezone."""
    d = dt_date(2025, 12, 9)
    result = get_datetime(
        d, "America/New_York", TARGET_TIMEZONE, use_start_of_day=False
    )
    assert result == datetime(
        2025, 12, 9, 23, 59, 59, tzinfo=ZoneInfo("America/Chicago")
    )


class _DummyGoogleEvent:
    """Minimal stub to mimic gcsa.event.Event for tests."""

    def __init__(
        self,
        *,
        start: datetime,
        end: datetime,
        timezone: str | None,
        summary: str,
        event_id: str,
        status: str = "confirmed",
    ) -> None:
        self.start = start
        self.end = end
        self.timezone = timezone
        self.summary = summary
        self.id = event_id
        self.other = {"status": status}
        self.created = start if start.tzinfo else start.replace(tzinfo=UTC)
        self.updated = end if end.tzinfo else end.replace(tzinfo=UTC)


def test_mapper_preserves_event_timezone_and_converts_to_utc() -> None:
    """Event timezone should be stored while datetimes are converted to UTC."""
    user_id = uuid4()
    calendar_id = uuid4()
    event_timezone = "America/New_York"
    google_event = _DummyGoogleEvent(
        start=datetime(2025, 1, 1, 9, 0, tzinfo=ZoneInfo(event_timezone)),
        end=datetime(2025, 1, 1, 10, 0, tzinfo=ZoneInfo(event_timezone)),
        timezone=event_timezone,
        summary="Morning sync",
        event_id="evt-1",
    )

    entry = GoogleCalendarMapper.to_calendar_entry(
        user_id=user_id,
        calendar_id=calendar_id,
        google_event=google_event,
        frequency=TaskFrequency.ONCE,
        target_timezone="America/Chicago",
    )

    assert entry.starts_at == datetime(2025, 1, 1, 14, 0, tzinfo=UTC)
    assert entry.ends_at == datetime(2025, 1, 1, 15, 0, tzinfo=UTC)
    assert entry.timezone == event_timezone


def test_mapper_falls_back_to_target_timezone_when_missing() -> None:
    """Fallback to target timezone when Google event has no timezone."""
    user_id = uuid4()
    calendar_id = uuid4()
    target_timezone = "America/Chicago"
    google_event = _DummyGoogleEvent(
        start=datetime(2025, 1, 1, 9, 0),
        end=datetime(2025, 1, 1, 10, 0),
        timezone=None,
        summary="No timezone",
        event_id="evt-2",
    )

    entry = GoogleCalendarMapper.to_calendar_entry(
        user_id=user_id,
        calendar_id=calendar_id,
        google_event=google_event,
        frequency=TaskFrequency.ONCE,
        target_timezone=target_timezone,
    )

    assert entry.starts_at == datetime(2025, 1, 1, 15, 0, tzinfo=UTC)
    assert entry.ends_at == datetime(2025, 1, 1, 16, 0, tzinfo=UTC)
    assert entry.timezone == target_timezone


def test_mapper_sets_category_when_provided() -> None:
    """Provided category should be applied to the entry."""
    user_id = uuid4()
    calendar_id = uuid4()
    google_event = _DummyGoogleEvent(
        start=datetime(2025, 1, 1, 9, 0, tzinfo=ZoneInfo("UTC")),
        end=datetime(2025, 1, 1, 10, 0, tzinfo=ZoneInfo("UTC")),
        timezone="UTC",
        summary="Categorized event",
        event_id="evt-3",
    )

    entry = GoogleCalendarMapper.to_calendar_entry(
        user_id=user_id,
        calendar_id=calendar_id,
        google_event=google_event,
        frequency=TaskFrequency.ONCE,
        target_timezone="UTC",
        category=EventCategory.WORK,
    )

    assert entry.category == EventCategory.WORK
