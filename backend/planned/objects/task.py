from datetime import date as dt_date, datetime, time
from enum import Enum
from typing import TYPE_CHECKING, Optional

from .base import BaseObject


class TaskType(str, Enum):
    EVENT = "EVENT"
    CHORE = "CHORE"
    ERRAND = "ERRAND"
    ACTIVITY = "ACTIVITY"


class TaskStatus(str, Enum):
    COMPLETE = "COMPLETE"
    NOT_READY = "NOT_READY"
    READY = "READY"
    PUNTED = "PUNTED"


class TimingType(str, Enum):
    DEADLINE = "DEADLINE"
    FIXED_TIME = "FIXED_TIME"
    TIME_WINDOW = "TIME_WINDOW"
    FLEXIBLE = "FLEXIBLE"


class TaskDefinition(BaseObject):
    id: str
    name: str
    description: str
    type: TaskType


class TaskSchedule(BaseObject):
    available_time: time | None = None
    start_time: time | None = None
    end_time: time | None = None
    timing_type: TimingType


class Task(BaseObject):
    date: dt_date
    status: TaskStatus
    task_definition: TaskDefinition
    completed_at: datetime | None = None
    schedule: TaskSchedule | None = None
    routine_id: str | None = None

    @property
    def id(self) -> str:
        return f"{self.date}:{self.task_definition.id}"
