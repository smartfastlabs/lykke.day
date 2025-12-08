import asyncio
import datetime

from loguru import logger

from planned import objects
from planned.objects import DayContext, DayTemplate, Task, TaskStatus
from planned.objects.user_settings import user_settings
from planned.repositories import (
    day_repo,
    day_template_repo,
    event_repo,
    message_repo,
    routine_repo,
    task_definition_repo,
    task_repo,
)
from planned.utils.dates import get_current_date

from .base import BaseService
from .day import DayService


def is_routine_active(schedule: objects.RoutineSchedule, date: datetime.date) -> bool:
    if not schedule.weekdays:
        return True
    return date.weekday() in schedule.weekdays


def get_starting_task_status(routine: objects.Routine) -> TaskStatus:
    if not routine.task_schedule or routine.task_schedule.available_time:
        return TaskStatus.NOT_READY

    return TaskStatus.READY


class PlanningService(BaseService):
    async def preview_tasks(self, date: datetime.date) -> list[Task]:
        result: list[Task] = []
        for routine in await routine_repo.all():
            logger.info(routine)
            if is_routine_active(routine.routine_schedule, date):
                task = objects.Task(
                    name=f"Routine: {routine.name}",
                    frequency=routine.routine_schedule.frequency,
                    routine_id=routine.id,
                    task_definition=await task_definition_repo.get(
                        routine.task_definition_id,
                    ),
                    schedule=routine.task_schedule,
                    scheduled_date=date,
                    status=get_starting_task_status(routine),
                    category=routine.category,
                )
                result.append(task)

        return result

    async def preview(self, date: datetime.date) -> DayContext:
        template: DayTemplate = await day_template_repo.get(
            user_settings.template_defaults[date.weekday()],
        )

        result: DayContext = DayContext(
            day=DayService.base_day(date, template=template),
        )
        result.tasks, result.events, result.messages = await asyncio.gather(
            self.preview_tasks(date),
            event_repo.search(date),
            message_repo.search(date),
        )

        return result

    async def unschedule(self, date: datetime.date) -> None:
        await task_repo.delete_by_date(
            date,
            lambda t: t.routine_id is not None,
        )
        day = await DayService.get_or_create(date)
        day.status = objects.DayStatus.UNSCHEDULED
        await day_repo.put(day)

    async def schedule(
        self,
        date: datetime.date,
    ) -> objects.DayContext:
        await task_repo.delete_by_date(date)

        result: objects.DayContext = await self.preview(date)
        result.day.status = "SCHEDULED"
        await asyncio.gather(
            day_repo.put(result.day),
            *[task_repo.put(task) for task in result.tasks],
        )

        return result


planning_svc = PlanningService()
