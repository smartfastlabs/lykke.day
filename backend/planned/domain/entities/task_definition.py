from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

from .. import value_objects
from ..value_objects.update import TaskDefinitionUpdateObject
from .base import BaseEntityObject

if TYPE_CHECKING:
    from ..events.task_events import TaskDefinitionUpdatedEvent


@dataclass(kw_only=True)
class TaskDefinitionEntity(BaseEntityObject[TaskDefinitionUpdateObject, "TaskDefinitionUpdatedEvent"]):
    user_id: UUID
    name: str
    description: str
    type: value_objects.TaskType
