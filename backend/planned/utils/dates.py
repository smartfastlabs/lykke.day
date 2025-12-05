import datetime
from zoneinfo import ZoneInfo

from planned import settings


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
