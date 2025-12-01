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

    def model_post_init(self, __context):  # type: ignore
        super().model_post_init(__context)
        self.id = str(self.date)
