from planned.domain.entities import Calendar

from .base import BaseCrudRepository
from .base.schema import calendars


class CalendarRepository(BaseCrudRepository[Calendar]):
    Object = Calendar
    table = calendars
