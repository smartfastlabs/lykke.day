from planned.domain.entities.routine import Routine

from .base import BaseConfigRepository
from .base.schema import routines


class RoutineRepository(BaseConfigRepository[Routine]):
    Object = Routine
    table = routines
