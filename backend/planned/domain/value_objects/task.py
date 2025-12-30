from datetime import time
from enum import Enum

from pydantic import BaseModel


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
    NOT_STARTED = "NOT_STARTED"
    PENDING = "PENDING"


class TimingType(str, Enum):
    DEADLINE = "DEADLINE"
    FIXED_TIME = "FIXED_TIME"
    TIME_WINDOW = "TIME_WINDOW"
    FLEXIBLE = "FLEXIBLE"


class TaskSchedule(BaseModel):
    available_time: time | None = None
    start_time: time | None = None
    end_time: time | None = None
    timing_type: TimingType

    def __bool__(self) -> bool:
        for foo in (
            self.available_time,
            self.start_time,
            self.end_time,
        ):
            if foo is not None:
                return True
        return False
