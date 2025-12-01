from planned.objects import TaskDefinition

from .base import BaseConfigRepository


class TaskDefinitionRepository(BaseConfigRepository[TaskDefinition]):
    Object = TaskDefinition
    _prefix = "config/task-definitions"
