from datetime import date, datetime, time
from enum import Enum

from .base import BaseObject


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


class Frequency(str, Enum):
    DAILY = "DAILY"
    CUSTOM_WEEKLY = "CUSTOM_WEEKLY"


class Category(str, Enum):
    HYGIENE = "hygiene"
    NUTRITION = "nutrition"
    HEALTH = "health"
    PET = "pet"
    CHORE = "chore"


class DayOfWeek(int, Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class Routine(BaseObject):
    id: str
    name: str
    description: str

    timing_type: TimingType
    frequency: Frequency
    category: Category

    # Optional time fields; Pydantic will parse "HH:MM" strings into datetime.time
    available_time: time | None = None
    start_time: time | None = None
    end_time: time | None = None

    schedule_days: list[DayOfWeek] | None = None


class Task(BaseObject):
    routine: Routine
    date: date
    status: TaskStatus
    completed_at: datetime | None = None

    @property
    def id(self) -> str:
        return self.routine.id
