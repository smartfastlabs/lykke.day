"""Routine schema."""

from datetime import time
from uuid import UUID

from pydantic import Field

from lykke.domain.value_objects.routine_definition import DayOfWeek
from lykke.domain.value_objects.task import TaskCategory, TaskFrequency

from .base import BaseEntitySchema, BaseSchema
from .task import TaskScheduleSchema


class RecurrenceScheduleSchema(BaseSchema):
    """API schema for RecurrenceSchedule value object."""

    frequency: TaskFrequency
    weekdays: list[DayOfWeek] | None = None
    day_number: int | None = None


class TimeWindowSchema(BaseSchema):
    """API schema for TimeWindow value object."""

    available_time: time | None = None
    start_time: time | None = None
    end_time: time | None = None
    cutoff_time: time | None = None


class RoutineDefinitionTaskSchema(BaseSchema):
    """API schema for RoutineDefinitionTask value object."""

    id: UUID | None = None
    task_definition_id: UUID
    name: str | None = None
    schedule: TaskScheduleSchema | None = None
    task_schedule: RecurrenceScheduleSchema | None = None
    time_window: TimeWindowSchema | None = None


class RoutineDefinitionCreateSchema(BaseSchema):
    """API schema for creating a RoutineDefinition entity."""

    name: str
    category: TaskCategory
    routine_definition_schedule: RecurrenceScheduleSchema
    description: str = ""
    time_window: TimeWindowSchema | None = None
    tasks: list[RoutineDefinitionTaskSchema] = Field(default_factory=list)


class RoutineDefinitionSchema(BaseEntitySchema):
    """API schema for RoutineDefinition entity."""

    user_id: UUID
    name: str
    category: TaskCategory
    routine_definition_schedule: RecurrenceScheduleSchema
    description: str = ""
    time_window: TimeWindowSchema | None = None
    tasks: list[RoutineDefinitionTaskSchema] = Field(default_factory=list)


class RoutineDefinitionUpdateSchema(BaseSchema):
    """API schema for RoutineDefinition update requests."""

    name: str | None = None
    category: TaskCategory | None = None
    routine_definition_schedule: RecurrenceScheduleSchema | None = None
    description: str | None = None
    time_window: TimeWindowSchema | None = None
    tasks: list[RoutineDefinitionTaskSchema] | None = None


class RoutineDefinitionTaskCreateSchema(BaseSchema):
    """API schema for attaching a RoutineDefinitionTask."""

    task_definition_id: UUID
    name: str | None = None
    schedule: TaskScheduleSchema | None = None
    task_schedule: RecurrenceScheduleSchema | None = None
    time_window: TimeWindowSchema | None = None


class RoutineDefinitionTaskUpdateSchema(BaseSchema):
    """API schema for updating an attached RoutineDefinitionTask."""

    name: str | None = None
    schedule: TaskScheduleSchema | None = None
    task_schedule: RecurrenceScheduleSchema | None = None
    time_window: TimeWindowSchema | None = None
