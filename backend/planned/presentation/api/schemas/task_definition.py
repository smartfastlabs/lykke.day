"""TaskDefinition schema."""

from uuid import UUID

from planned.domain.value_objects.task import TaskType

from .base import BaseEntitySchema


class TaskDefinition(BaseEntitySchema):
    """API schema for TaskDefinition entity."""

    user_id: UUID
    name: str
    description: str
    type: TaskType

