from planned.domain.entities import Day

from .base import BaseCrudRepository
from .base.schema import days


class DayRepository(BaseCrudRepository[Day]):
    Object = Day
    table = days
