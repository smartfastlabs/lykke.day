from planned.domain.entities import Task

from .base import BaseDateRepository
from .base.schema import tasks


class TaskRepository(BaseDateRepository[Task]):
    Object = Task
    table = tasks
