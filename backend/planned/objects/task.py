from datetime import date as dt_date, datetime, time
from enum import Enum
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field

from .base import BaseDateObject, BaseObject


class TaskTag(str, Enum):
    AVOIDANT = "AVOIDANT"
    FORGETTABLE = "FORGETTABLE"
    IMPORTANT = "IMPORTANT"
    URGENT = "URGENT"
    FUN = "FUN"


class TaskFrequency(str, Enum):
    DAILY = "DAILY"
    CUSTOM_WEEKLY = "CUSTOM_WEEKLY"
    WEEKLY = "WEEKLY"
    ONCE = "ONCE"
    YEARLY = "YEARLY"
    MONTHLY = "MONTHLY"
    BI_WEEKLY = "BI_WEEKLY"
    WEEK_DAYS = "WORK_DAYS"
    WEEKEND_DAYS = "WEEKENDS"


class TaskCategory(str, Enum):
    HYGIENE = "HYGIENE"
    NUTRITION = "NUTRITION"
    HEALTH = "HEALTH"
    PET = "PET"
    HOUSE = "HOUSE"


class TaskType(str, Enum):
    MEAL = "MEAL"
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


class TaskSchedule(BaseModel):
    available_time: time | None = None
    start_time: time | None = None
    end_time: time | None = None
    timing_type: TimingType


class Task(BaseDateObject):
    scheduled_date: dt_date
    name: str
    status: TaskStatus
    task_definition: TaskDefinition
    category: TaskCategory
    frequency: TaskFrequency
    completed_at: datetime | None = None
    schedule: TaskSchedule | None = None
    routine_id: str | None = None
    tags: list[TaskTag] = Field(default_factory=list)

    def _get_date(self) -> dt_date:
        return self.scheduled_date
