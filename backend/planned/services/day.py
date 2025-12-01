import asyncio
import datetime

from planned import objects
from planned.repositories import day_repo, event_repo, message_repo, task_repo
from planned.utils.dates import get_current_datetime

from .base import BaseService
from .routine import routine_svc


class DayService(BaseService):
    async def schedule_day(
        self,
        date: datetime.date,
    ) -> objects.DayContext:
        await asyncio.gather(
            routine_svc.schedule(date),
            day_repo.put(
                objects.Day(
                    date=date,
                    status=objects.DayStatus.SCHEDULED,
                    scheduled_at=get_current_datetime(),
                ),
                key=str(date),
            ),
        )

        return await self.load_day_context(date)

    async def load_day_context(
        self,
        date: datetime.date,
        schedule_routines: bool = True,
    ) -> objects.DayContext:
        tasks: list[objects.Task]
        events: list[objects.Event]
        messages: list[objects.Message]
        day: objects.Day

        tasks, events, messages, day = await asyncio.gather(
            task_repo.search(date),
            event_repo.search(date),
            message_repo.search(date),
            day_repo.get(str(date)),
        )

        if schedule_routines and not tasks:
            tasks = await routine_svc.schedule(date)

        return objects.DayContext(
            date=date,
            day=day,
            tasks=tasks,
            events=events,
            messages=messages,
        )


day_svc = DayService()
