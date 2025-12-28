import datetime
from zoneinfo import ZoneInfo

from planned.core.config import settings


def get_current_date() -> datetime.date:
    desired_timezone = ZoneInfo(settings.TIMEZONE)

    return datetime.datetime.now(tz=desired_timezone).date()


def get_current_datetime() -> datetime.datetime:
    desired_timezone = ZoneInfo(settings.TIMEZONE)

    return datetime.datetime.now(tz=desired_timezone)


def get_current_time() -> datetime.time:
    desired_timezone = ZoneInfo(settings.TIMEZONE)

    return datetime.datetime.now(tz=desired_timezone).time()


def get_tomorrows_date() -> datetime.date:
    return get_current_date() + datetime.timedelta(days=1)


def get_time_between(
    t1: datetime.time | datetime.datetime,
    t2: datetime.time | datetime.datetime | None = None,
) -> datetime.timedelta:
    today = get_current_date()

    if isinstance(t1, datetime.time):
        t1 = datetime.datetime.combine(today, t1)

    if not t2:
        t2 = get_current_datetime()

    elif isinstance(t2, datetime.time):
        t2 = datetime.datetime.combine(today, t2)

    return t1 - t2
