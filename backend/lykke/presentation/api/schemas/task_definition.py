"""TaskDefinition schema."""

from uuid import UUID

from lykke.domain.value_objects.task import TaskType

from .base import BaseEntitySchema, BaseSchema


class TaskDefinitionCreateSchema(BaseSchema):
    """API schema for creating a TaskDefinition entity."""

    name: str
    description: str
    type: TaskType


class TaskDefinitionSchema(TaskDefinitionCreateSchema, BaseEntitySchema):
    """API schema for TaskDefinition entity."""

    user_id: UUID


class TaskDefinitionUpdateSchema(BaseSchema):
    """API schema for TaskDefinition update requests."""

    name: str | None = None
    description: str | None = None
    type: TaskType | None = None
