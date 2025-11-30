from datetime import date as dt_date

from .base import BaseObject
from .event import Event
from .message import Message
from .task import Task


class Day(BaseObject):
    date: dt_date
    events: list[Event]
    tasks: list[Task]
    messages: list[Message]
