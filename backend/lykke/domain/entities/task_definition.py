from dataclasses import dataclass
from uuid import UUID

from lykke.domain import value_objects
from lykke.domain.entities.base import BaseEntityObject


@dataclass(kw_only=True)
class TaskDefinitionEntity(BaseEntityObject):
    user_id: UUID
    name: str
    description: str
    type: value_objects.TaskType
