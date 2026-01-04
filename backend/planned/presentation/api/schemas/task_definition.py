"""TaskDefinition schema."""

from uuid import UUID

from planned.domain.value_objects.task import TaskType

from .base import BaseEntitySchema, BaseSchema


class TaskDefinitionSchema(BaseEntitySchema):
    """API schema for TaskDefinition entity."""

    user_id: UUID
    name: str
    description: str
    type: TaskType


class TaskDefinitionUpdateSchema(BaseSchema):
    """API schema for TaskDefinition update requests."""

    name: str | None = None
    description: str | None = None
    type: TaskType | None = None

