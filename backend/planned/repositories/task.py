from planned.objects import Task

from .base import BaseDateRepository


class TaskRepository(BaseDateRepository[Task]):
    Object = Task
    _prefix = "tasks"
