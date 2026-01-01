import datetime
from datetime import UTC
from zoneinfo import ZoneInfo

from planned.core.config import settings


def get_current_date() -> datetime.date:
    """Get current date in the configured timezone."""
    desired_timezone = ZoneInfo(settings.TIMEZONE)
    return datetime.datetime.now(tz=desired_timezone).date()


def get_current_datetime() -> datetime.datetime:
    """Get current datetime in UTC."""
    return datetime.datetime.now(tz=UTC)


def get_current_time() -> datetime.time:
    """Get current time in the configured timezone."""
    desired_timezone = ZoneInfo(settings.TIMEZONE)
    return datetime.datetime.now(tz=desired_timezone).time()


def get_tomorrows_date() -> datetime.date:
    return get_current_date() + datetime.timedelta(days=1)


def get_time_between(
    t1: datetime.time | datetime.datetime,
    t2: datetime.time | datetime.datetime | None = None,
) -> datetime.timedelta:
    """Calculate time difference between two times/datetimes.
    
    All datetimes are converted to UTC for comparison.
    """
    today = get_current_date()
    desired_timezone = ZoneInfo(settings.TIMEZONE)

    if isinstance(t1, datetime.time):
        # Combine with today's date in the configured timezone, then convert to UTC
        t1 = datetime.datetime.combine(today, t1, tzinfo=desired_timezone).astimezone(UTC)

    if not t2:
        t2 = get_current_datetime()
    elif isinstance(t2, datetime.time):
        # Combine with today's date in the configured timezone, then convert to UTC
        t2 = datetime.datetime.combine(today, t2, tzinfo=desired_timezone).astimezone(UTC)

    return t1 - t2
