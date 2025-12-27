from planned.domain.entities import Task

from .base import BaseDateRepository


class TaskRepository(BaseDateRepository[Task]):
    Object = Task
    _prefix = "tasks"
