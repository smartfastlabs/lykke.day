from dataclasses import dataclass, field
from uuid import UUID

from .. import value_objects
from .base import BaseConfigObject


@dataclass(kw_only=True)
class Routine(BaseConfigObject):
    user_id: UUID
    name: str

    category: value_objects.TaskCategory
    routine_schedule: value_objects.RoutineSchedule
    description: str = ""
    tasks: list[value_objects.RoutineTask] = field(default_factory=list)
