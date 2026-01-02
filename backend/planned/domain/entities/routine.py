from uuid import UUID

from pydantic import Field

from .. import value_objects
from .base import BaseConfigObject


class Routine(BaseConfigObject):
    user_id: UUID
    name: str

    category: value_objects.TaskCategory
    routine_schedule: value_objects.RoutineSchedule
    description: str = ""
    tasks: list[value_objects.RoutineTask] = Field(default_factory=list)
