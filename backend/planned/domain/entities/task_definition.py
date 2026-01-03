from dataclasses import dataclass
from uuid import UUID

from .. import value_objects
from .base import BaseEntityObject


@dataclass(kw_only=True)
class TaskDefinition(BaseEntityObject):
    user_id: UUID
    name: str
    description: str
    type: value_objects.TaskType
