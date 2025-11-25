import datetime

from planned.objects.routine import Routine, RoutineInstance, RoutineInstanceStatus
from planned.utils.json import read_directory

from .base import BaseRepository


class RoutineRepository(BaseRepository[Routine]):
    Object = Routine
    _prefix = "routines"

    async def get_instances(self, date: datetime.date) -> list[RoutineInstance]:
        return read_directory(
            f"routines/instances/{date}",
            RoutineInstance,
        )

    async def update_routine(
        self, routine_id: str, status: RoutineInstanceStatus
    ) -> RoutineInstance:
        pass
