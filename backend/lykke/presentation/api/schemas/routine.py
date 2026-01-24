"""Routine schemas."""

from uuid import UUID

from lykke.domain.value_objects import TaskCategory

from .base import BaseDateSchema
from .routine_definition import TimeWindowSchema


class RoutineSchema(BaseDateSchema):
    """API schema for Routine entity."""

    user_id: UUID
    routine_definition_id: UUID
    name: str
    category: TaskCategory
    description: str
    time_window: TimeWindowSchema | None = None
