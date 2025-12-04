from datetime import date, datetime, time
from enum import Enum
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel

from .base import BaseObject
from .task import TaskCategory, TaskFrequency, TaskSchedule


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


class Routine(BaseObject):
    name: str
    task_definition_id: str

    category: TaskCategory
    routine_schedule: RoutineSchedule
    description: str = ""
    task_schedule: TaskSchedule | None = None
