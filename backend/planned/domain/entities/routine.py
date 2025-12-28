from pydantic import Field

from ..value_objects.routine import RoutineSchedule, RoutineTask
from ..value_objects.task import TaskCategory
from .base import BaseConfigObject


class Routine(BaseConfigObject):
    name: str

    category: TaskCategory
    routine_schedule: RoutineSchedule
    description: str = ""
    tasks: list[RoutineTask] = Field(default_factory=list)
