import datetime

from loguru import logger

from planned import objects
from planned.objects import Task, TaskStatus
from planned.repositories import routine_repo, task_definition_repo, task_repo
from planned.utils.dates import get_current_date

from .base import BaseService


def is_routine_active(schedule: objects.RoutineSchedule, date: datetime.date) -> bool:
    if not schedule.weekdays:
        return True
    return date.weekday() in schedule.weekdays


def get_starting_task_status(routine: objects.Routine) -> TaskStatus:
    if not routine.task_schedule or routine.task_schedule.available_time:
        return TaskStatus.NOT_READY

    return TaskStatus.READY


class RoutineService(BaseService):
    async def schedule(self, date: datetime.date | None = None) -> list[Task]:
        if date is None:
            date = get_current_date()

        await task_repo.delete_by_date(date)
        result: list[Task] = []

        for routine in await routine_repo.all():
            logger.info(routine)
            if is_routine_active(routine.routine_schedule, date):
                task = objects.Task(
                    id=f"{routine.id}-{date}",
                    routine_id=routine.id,
                    task_definition=await task_definition_repo.get(
                        routine.task_definition_id,
                    ),
                    schedule=routine.task_schedule,
                    scheduled_date=date,
                    status=get_starting_task_status(routine),
                )
                result.append(await task_repo.put(task))

        return result


routine_svc = RoutineService()
