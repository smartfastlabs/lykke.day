from planned.objects import Calendar

from .base import BaseRepository


class CalendarRepository(BaseRepository[Calendar]):
    Object = Calendar
    _prefix = "calendars"
