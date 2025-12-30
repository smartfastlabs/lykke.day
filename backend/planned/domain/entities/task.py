from datetime import date as dt_date
from datetime import datetime
from uuid import UUID

from pydantic import Field

from ..value_objects.task import (
    TaskCategory,
    TaskFrequency,
    TaskSchedule,
    TaskStatus,
    TaskTag,
)
from .action import Action
from .base import BaseDateObject
from .task_definition import TaskDefinition


class Task(BaseDateObject):
    user_id: UUID
    scheduled_date: dt_date
    name: str
    status: TaskStatus
    task_definition: TaskDefinition
    category: TaskCategory
    frequency: TaskFrequency
    completed_at: datetime | None = None
    schedule: TaskSchedule | None = None
    routine_id: UUID | None = None
    tags: list[TaskTag] = Field(default_factory=list)
    actions: list[Action] = Field(default_factory=list)

    def _get_date(self) -> dt_date:
        return self.scheduled_date
