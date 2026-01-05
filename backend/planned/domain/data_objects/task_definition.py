from dataclasses import dataclass
from uuid import UUID

from planned.domain import value_objects
from planned.domain.entities.base import BaseEntityObject


@dataclass(kw_only=True)
class TaskDefinition(BaseEntityObject):
    user_id: UUID
    name: str
    description: str
    type: value_objects.TaskType

