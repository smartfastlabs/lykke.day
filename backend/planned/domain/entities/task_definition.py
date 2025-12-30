from uuid import UUID

from ..value_objects.task import TaskType
from .base import BaseEntityObject


class TaskDefinition(BaseEntityObject):
    user_uuid: UUID
    name: str
    description: str
    type: TaskType

