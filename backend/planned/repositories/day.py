from planned.objects import Day

from .base import BaseRepository


class DayRepository(BaseRepository[Day]):
    Object = Day
    _prefix = "days"
