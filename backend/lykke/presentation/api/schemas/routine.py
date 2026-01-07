"""Routine schema."""

from uuid import UUID

from pydantic import Field
from lykke.domain.value_objects.routine import RoutineSchedule, RoutineTask
from lykke.domain.value_objects.task import TaskCategory, TaskSchedule

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


class RoutineTaskCreateSchema(BaseSchema):
    """API schema for attaching a RoutineTask."""

    task_definition_id: UUID
    name: str | None = None
    schedule: TaskSchedule | None = None


class RoutineTaskUpdateSchema(BaseSchema):
    """API schema for updating an attached RoutineTask."""

    name: str | None = None
    schedule: TaskSchedule | None = None
