from uuid import UUID

from .. import value_objects
from .base import BaseEntityObject


class TaskDefinition(BaseEntityObject):
    user_id: UUID
    name: str
    description: str
    type: value_objects.TaskType
