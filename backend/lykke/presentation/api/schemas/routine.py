"""Routine schema."""

from uuid import UUID

from pydantic import Field

from lykke.domain.value_objects.routine import DayOfWeek
from lykke.domain.value_objects.task import TaskCategory, TaskFrequency

from .base import BaseEntitySchema, BaseSchema
from .task import TaskScheduleSchema


class RecurrenceScheduleSchema(BaseSchema):
    """API schema for RecurrenceSchedule value object."""

    frequency: TaskFrequency
    weekdays: list[DayOfWeek] | None = None
    day_number: int | None = None


class RoutineTaskSchema(BaseSchema):
    """API schema for RoutineTask value object."""

    id: UUID | None = None
    task_definition_id: UUID
    name: str | None = None
    schedule: TaskScheduleSchema | None = None
    task_schedule: RecurrenceScheduleSchema | None = None


class RoutineCreateSchema(BaseSchema):
    """API schema for creating a Routine entity."""

    name: str
    category: TaskCategory
    routine_schedule: RecurrenceScheduleSchema
    description: str = ""
    tasks: list[RoutineTaskSchema] = Field(default_factory=list)


class RoutineSchema(BaseEntitySchema):
    """API schema for Routine entity."""

    user_id: UUID
    name: str
    category: TaskCategory
    routine_schedule: RecurrenceScheduleSchema
    description: str = ""
    tasks: list[RoutineTaskSchema] = Field(default_factory=list)


class RoutineUpdateSchema(BaseSchema):
    """API schema for Routine update requests."""

    name: str | None = None
    category: TaskCategory | None = None
    routine_schedule: RecurrenceScheduleSchema | None = None
    description: str | None = None
    tasks: list[RoutineTaskSchema] | None = None


class RoutineTaskCreateSchema(BaseSchema):
    """API schema for attaching a RoutineTask."""

    task_definition_id: UUID
    name: str | None = None
    schedule: TaskScheduleSchema | None = None
    task_schedule: RecurrenceScheduleSchema | None = None


class RoutineTaskUpdateSchema(BaseSchema):
    """API schema for updating an attached RoutineTask."""

    name: str | None = None
    schedule: TaskScheduleSchema | None = None
    task_schedule: RecurrenceScheduleSchema | None = None
