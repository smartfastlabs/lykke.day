"""Date and time utility functions."""

import datetime
from datetime import UTC
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def ensure_utc(dt: datetime.datetime | str | None) -> datetime.datetime | None:
    """Return a datetime guaranteed to be timezone-aware in UTC."""
    if dt is None:
        return None
    if isinstance(dt, str):
        normalized = dt.replace("Z", "+00:00")
        try:
            parsed = datetime.datetime.fromisoformat(normalized)
        except ValueError:
            return None
        dt = parsed
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def resolve_timezone(timezone: str | None) -> datetime.tzinfo:
    """Resolve a timezone string to tzinfo with UTC fallback."""
    if timezone:
        try:
            return ZoneInfo(timezone)
        except (ZoneInfoNotFoundError, ValueError):
            return UTC
    return UTC


def get_current_date(timezone: str | None = None) -> datetime.date:
    """Get current date in the provided timezone (UTC fallback)."""
    desired_timezone = resolve_timezone(timezone)
    return datetime.datetime.now(tz=desired_timezone).date()


def get_current_datetime() -> datetime.datetime:
    """Get current datetime in UTC."""
    return datetime.datetime.now(tz=UTC)


def get_current_datetime_in_timezone(
    timezone: str | None,
) -> datetime.datetime:
    """Get current datetime in a specific timezone."""
    desired_timezone = resolve_timezone(timezone)
    return datetime.datetime.now(tz=desired_timezone)


def get_current_time(timezone: str | None = None) -> datetime.time:
    """Get current time in the provided timezone (UTC fallback)."""
    desired_timezone = resolve_timezone(timezone)
    return datetime.datetime.now(tz=desired_timezone).time()


def get_tomorrows_date(timezone: str | None = None) -> datetime.date:
    """Get tomorrow's date in the provided timezone (UTC fallback)."""
    return get_current_date(timezone) + datetime.timedelta(days=1)


def get_time_between(
    t1: datetime.time | datetime.datetime,
    t2: datetime.time | datetime.datetime | None = None,
    *,
    timezone: str | None = None,
) -> datetime.timedelta:
    """Calculate time difference between two times/datetimes.
    
    All datetimes are converted to UTC for comparison.
    """
    today = get_current_date(timezone)
    desired_timezone = resolve_timezone(timezone)

    if isinstance(t1, datetime.time):
        # Combine with today's date in the configured timezone, then convert to UTC
        t1 = datetime.datetime.combine(today, t1, tzinfo=desired_timezone).astimezone(UTC)

    if not t2:
        t2 = get_current_datetime()
    elif isinstance(t2, datetime.time):
        # Combine with today's date in the configured timezone, then convert to UTC
        t2 = datetime.datetime.combine(today, t2, tzinfo=desired_timezone).astimezone(UTC)

    return t1 - t2

