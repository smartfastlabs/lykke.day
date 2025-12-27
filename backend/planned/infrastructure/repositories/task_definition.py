from planned.domain.entities import TaskDefinition

from .base import BaseConfigRepository
from .base.schema import task_definitions


class TaskDefinitionRepository(BaseConfigRepository[TaskDefinition]):
    Object = TaskDefinition
    table = task_definitions
