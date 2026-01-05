from dataclasses import dataclass
from uuid import UUID

from .. import value_objects
from ..events.task_events import TaskDefinitionUpdatedEvent
from ..value_objects.update import TaskDefinitionUpdateObject
from .base import BaseEntityObject


@dataclass(kw_only=True)
class TaskDefinitionEntity(BaseEntityObject[TaskDefinitionUpdateObject, TaskDefinitionUpdatedEvent]):
    user_id: UUID
    name: str
    description: str
    type: value_objects.TaskType
