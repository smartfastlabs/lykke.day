from datetime import date as dt_date

from .base import BaseObject
from .event import Event
from .routine import Task


class Day(BaseObject):
    date: dt_date
    events: list[Event]
    tasks: list[Task]
