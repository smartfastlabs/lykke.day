from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

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
    day_number: int | None = (
        None  # Day of month (1-31) for MONTHLY, day of year (1-365) for YEARLY
    )


class RoutineTask(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    task_definition_id: UUID
    name: str | None = None
    schedule: TaskSchedule | None = None
