
from datetime import date as dt_date

from .base import BaseObject
from .event import Event
from .routine import RoutineInstance


class Day(BaseObject):
    date: dt_date
    events: list[Event]
    routine_instances: list[RoutineInstance]
