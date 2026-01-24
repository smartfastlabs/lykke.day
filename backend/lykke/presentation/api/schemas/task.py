"""Task schema."""

from datetime import date, datetime, time
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from pydantic import Field

from lykke.domain.value_objects.task import (
    TaskCategory,
    TaskFrequency,
    TaskStatus,
    TaskTag,
    TaskType,
    TimingType,
)

from .base import BaseEntitySchema, BaseSchema

if TYPE_CHECKING:
    from .action import ActionSchema


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
    type: TaskType
    description: str | None = None
    category: TaskCategory
    frequency: TaskFrequency
    completed_at: datetime | None = None
    schedule: TaskScheduleSchema | None = None
    routine_definition_id: UUID | None = None
    tags: list[TaskTag] = Field(default_factory=list)
    actions: list["ActionSchema"] = Field(default_factory=list)


class AdhocTaskCreateSchema(BaseSchema):
    """API schema for creating adhoc tasks."""

    scheduled_date: date
    name: str
    description: str | None = None
    category: TaskCategory
    schedule: TaskScheduleSchema | None = None
    tags: list[TaskTag] = Field(default_factory=list)
