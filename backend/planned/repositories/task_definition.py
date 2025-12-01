from planned.objects import TaskDefinition

from .base import BaseRepository


class TaskDefinitionRepository(BaseRepository[TaskDefinition]):
    Object = TaskDefinition
    _prefix = "config/task-definitions"
