
from datetime import date, datetime
from enum import Enum

from .base import BaseObject
from .routine import Routine


class TaskStatus(str, Enum):
    COMPLETE = "COMPLETE"
    NOT_READY = "NOT_READY"
    READY = "READY"
    PUNTED = "PUNTED"


class Task(BaseObject):
    routine: Routine
    date: date
    status: TaskStatus
    completed_at: datetime | None = None

    @property
    def id(self) -> str:
        return self.routine.id
