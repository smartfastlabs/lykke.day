from planned.objects import Calendar

from .base import BaseCrudRepository


class CalendarRepository(BaseCrudRepository[Calendar]):
    Object = Calendar
    _prefix = "calendars"
