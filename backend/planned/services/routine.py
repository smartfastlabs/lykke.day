import datetime

from loguru import logger

from planned import objects
from planned.objects import Task, TaskStatus
from planned.repositories import task_repo, routine_repo
from planned.utils.dates import get_current_date

from .base import BaseService


def is_routine_active(routine: objects.Routine, date: datetime.date) -> bool:
    return not (routine.schedule_days and date.weekday() not in routine.schedule_days)


class RoutineService(BaseService):
    async def schedule(
        self, date: datetime.date | None = None
    ) -> list[Task]:
        if date is None:
            date = get_current_date()

        await task_repo.delete_by_date(date)
        result: list[Task] = []

        for routine in await routine_repo.search():
            logger.info(routine)
            if is_routine_active(routine, date):
                result.append(
                    objects.Task(
                        routine=routine,
                        date=date,
                        status=TaskStatus.NOT_READY
                        if routine.available_time
                        else TaskStatus.READY,
                    )
                )

        return result


routine_svc = RoutineService()
