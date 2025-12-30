from uuid import UUID

from ..value_objects.task import TaskType
from .base import BaseEntityObject


class TaskDefinition(BaseEntityObject):
    user_id: UUID
    name: str
    description: str
    type: TaskType

