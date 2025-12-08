from datetime import datetime
from zoneinfo import ZoneInfo

from dateutil.tz import tzoffset

from planned.objects.event import get_datetime


def test_get_datetime():
    google_dt = datetime(2025, 12, 9, 10, 30, tzinfo=tzoffset(None, -21600))
    google_tz = "America/New_York"

    assert get_datetime(
        google_dt,
        google_tz,
    ) == datetime(2025, 12, 9, 10, 30).replace(tzinfo=ZoneInfo("America/Chicago"))


from datetime import date, time


def test_get_datetime_with_aware_datetime():
    """Datetime with tzinfo should convert to settings.TIMEZONE."""
    google_dt = datetime(2025, 12, 9, 10, 30, tzinfo=tzoffset(None, -21600))
    google_tz = "America/New_York"
    assert get_datetime(google_dt, google_tz) == datetime(
        2025, 12, 9, 10, 30, tzinfo=ZoneInfo("America/Chicago")
    )


def test_get_datetime_with_aware_datetime_different_offset():
    """Datetime in UTC should convert correctly to Chicago."""
    # 16:30 UTC = 10:30 Chicago (UTC-6 in winter)
    utc_dt = datetime(2025, 12, 9, 16, 30, tzinfo=ZoneInfo("UTC"))
    assert get_datetime(utc_dt, "UTC") == datetime(
        2025, 12, 9, 10, 30, tzinfo=ZoneInfo("America/Chicago")
    )


def test_get_datetime_with_naive_datetime():
    """Naive datetime should use provided timezone, then convert."""
    # 11:30 in New York = 10:30 in Chicago (both UTC-5 and UTC-6 in winter)
    naive_dt = datetime(2025, 12, 9, 11, 30)
    result = get_datetime(naive_dt, "America/New_York")
    assert result == datetime(2025, 12, 9, 10, 30, tzinfo=ZoneInfo("America/Chicago"))


def test_get_datetime_with_date_start_of_day():
    """Date should become midnight in settings.TIMEZONE."""
    d = date(2025, 12, 9)
    result = get_datetime(d, "America/New_York", use_start_of_day=True)
    assert result == datetime(2025, 12, 9, 0, 0, 0, tzinfo=ZoneInfo("America/Chicago"))


def test_get_datetime_with_date_end_of_day():
    """Date should become 23:59:59 in settings.TIMEZONE."""
    d = date(2025, 12, 9)
    result = get_datetime(d, "America/New_York", use_start_of_day=False)
    assert result == datetime(
        2025, 12, 9, 23, 59, 59, tzinfo=ZoneInfo("America/Chicago")
    )
