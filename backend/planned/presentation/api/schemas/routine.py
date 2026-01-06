"""Routine schema."""

from uuid import UUID

from planned.domain.value_objects.routine import RoutineSchedule, RoutineTask
from planned.domain.value_objects.task import TaskCategory
from pydantic import Field

from .base import BaseEntitySchema, BaseSchema


class RoutineCreateSchema(BaseSchema):
    """API schema for creating a Routine entity."""

    name: str
    category: TaskCategory
    routine_schedule: RoutineSchedule
    description: str = ""
    tasks: list[RoutineTask] = Field(default_factory=list)


class RoutineSchema(BaseEntitySchema):
    """API schema for Routine entity."""

    user_id: UUID
    name: str
    category: TaskCategory
    routine_schedule: RoutineSchedule
    description: str = ""
    tasks: list[RoutineTask] = Field(default_factory=list)


class RoutineUpdateSchema(BaseSchema):
    """API schema for Routine update requests."""

    name: str | None = None
    category: TaskCategory | None = None
    routine_schedule: RoutineSchedule | None = None
    description: str | None = None
    tasks: list[RoutineTask] | None = None
