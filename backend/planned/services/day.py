import asyncio
import datetime

from planned import objects
from planned.repositories import event_repo, message_repo, task_repo

from .base import BaseService
from .routine import routine_svc


class DayService(BaseService):
    async def schedule_day(
        self,
        date: datetime.date,
    ) -> objects.Day:
        await routine_svc.schedule(date)

        return await self.load_day(date)

    async def load_day(
        self,
        date: datetime.date,
        schedule_routines: bool = True,
    ) -> objects.Day:
        tasks: list[objects.Task]
        events: list[objects.Event]
        messages: list[objects.Message]

        tasks, events, messages = await asyncio.gather(
            task_repo.search(date),
            event_repo.search(date),
            message_repo.search(date),
        )

        if schedule_routines and not tasks:
            tasks = await routine_svc.schedule(date)

        return objects.Day(
            date=date,
            tasks=tasks,
            events=events,
            messages=messages,
        )


day_svc = DayService()
