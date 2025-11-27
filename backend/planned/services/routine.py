import datetime

from loguru import logger

from planned import objects
from planned.objects import RoutineInstance, RoutineInstanceStatus
from planned.repositories import routine_instance_repo, routine_repo
from planned.utils.dates import get_current_date

from .base import BaseService


def is_routine_active(routine: objects.Routine, date: datetime.date) -> bool:
    return not (routine.schedule_days and date.weekday() not in routine.schedule_days)


class RoutineService(BaseService):
    async def schedule(
        self, date: datetime.date | None = None
    ) -> list[RoutineInstance]:
        if date is None:
            date = get_current_date()

        await routine_instance_repo.delete_by_date(date)
        result: list[RoutineInstance] = []

        for routine in await routine_repo.search():
            logger.info(routine)
            if is_routine_active(routine, date):
                result.append(
                    objects.RoutineInstance(
                        routine=routine,
                        date=date,
                        status=RoutineInstanceStatus.NOT_READY
                        if routine.available_time
                        else RoutineInstanceStatus.READY,
                    )
                )

        return result


routine_svc = RoutineService()
