from planned.objects.routine import Routine

from .base import BaseRepository


class RoutineRepository(BaseRepository[Routine]):
    Object = Routine
    _prefix = "config/routines"
