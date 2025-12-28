from enum import Enum

from pydantic import BaseModel

from .task import TaskFrequency, TaskSchedule


class DayOfWeek(int, Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class RoutineSchedule(BaseModel):
    frequency: TaskFrequency
    weekdays: list[DayOfWeek] | None = None


class RoutineTask(BaseModel):
    task_definition_id: str
    name: str | None = None
    schedule: TaskSchedule | None = None

