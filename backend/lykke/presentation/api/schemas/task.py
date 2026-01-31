"""Task schema."""

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import Field

from lykke.domain.value_objects.task import (
    TaskCategory,
    TaskFrequency,
    TaskStatus,
    TaskTag,
    TaskType,
)
from lykke.domain.value_objects.timing_status import TimingStatus

from .base import BaseEntitySchema, BaseSchema
from .routine_definition import TimeWindowSchema

if TYPE_CHECKING:
    from .action import ActionSchema


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
    snoozed_until: datetime | None = None
    time_window: TimeWindowSchema | None = None
    routine_definition_id: UUID | None = None
    timing_status: TimingStatus | None = None
    next_available_time: datetime | None = None
    tags: list[TaskTag] = Field(default_factory=list)
    actions: list["ActionSchema"] = Field(default_factory=list)


class AdhocTaskCreateSchema(BaseSchema):
    """API schema for creating adhoc or reminder tasks."""

    scheduled_date: date
    name: str
    type: TaskType = TaskType.ADHOC
    description: str | None = None
    category: TaskCategory
    time_window: TimeWindowSchema | None = None
    tags: list[TaskTag] = Field(default_factory=list)
