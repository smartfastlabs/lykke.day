"""Task schema."""

from typing import TYPE_CHECKING, Optional

from datetime import date, datetime, time
from uuid import UUID

from pydantic import Field

from planned.domain.value_objects.task import (
    TaskCategory,
    TaskFrequency,
    TaskStatus,
    TaskTag,
    TimingType,
)

from .base import BaseEntitySchema, BaseSchema

if TYPE_CHECKING:
    from .action import ActionSchema
    from .task_definition import TaskDefinitionSchema


class TaskScheduleSchema(BaseSchema):
    """API schema for TaskSchedule value object."""

    available_time: time | None = None
    start_time: time | None = None
    end_time: time | None = None
    timing_type: TimingType


class TaskSchema(BaseEntitySchema):
    """API schema for Task entity."""

    user_id: UUID
    scheduled_date: date
    name: str
    status: TaskStatus
    task_definition: "TaskDefinitionSchema"
    category: TaskCategory
    frequency: TaskFrequency
    completed_at: datetime | None = None
    schedule: Optional[TaskScheduleSchema] = None
    routine_id: UUID | None = None
    tags: list[TaskTag] = Field(default_factory=list)
    actions: list["ActionSchema"] = Field(default_factory=list)

