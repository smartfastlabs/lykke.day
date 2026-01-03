"""Routine schema."""

from uuid import UUID

from pydantic import Field

from planned.domain.value_objects.routine import RoutineSchedule, RoutineTask
from planned.domain.value_objects.task import TaskCategory

from .base import BaseEntitySchema


class RoutineSchema(BaseEntitySchema):
    """API schema for Routine entity."""

    user_id: UUID
    name: str
    category: TaskCategory
    routine_schedule: RoutineSchedule
    description: str = ""
    tasks: list[RoutineTask] = Field(default_factory=list)

