import datetime

from planned.objects.routine import Routine, RoutineInstance, RoutineInstanceStatus
from planned.utils.json import read_directory

from .base import BaseRepository


class RoutineRepository(BaseRepository[Routine]):
    Object = Routine
    _prefix = "routines"