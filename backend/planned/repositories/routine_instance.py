
from planned.objects.routine import RoutineInstance

from .base import BaseRepository


class RoutineInstanceRepository(BaseRepository[RoutineInstance]):
    Object = RoutineInstance
    _prefix = "routine_instances"
