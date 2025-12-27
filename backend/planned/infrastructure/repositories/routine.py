from planned.domain.entities.routine import Routine

from .base import BaseConfigRepository


class RoutineRepository(BaseConfigRepository[Routine]):
    Object = Routine
    _prefix = "config/routines"
