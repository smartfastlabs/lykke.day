import asyncio
import datetime
from collections.abc import Awaitable, Callable
from typing import Protocol, TypeVar, cast

from planned import exceptions, objects
from planned.repositories import day_repo, event_repo, message_repo, task_repo
from planned.utils.dates import get_current_date, get_current_datetime

from .base import BaseService
from .routine import routine_svc

T = TypeVar("T", bound=objects.BaseDateObject)


class HasId[IdT](Protocol):
    @property
    def id(self) -> IdT: ...


U = TypeVar("U", bound=HasId)


def replace(lst: list[T], obj: T) -> None:
    for i, item in enumerate(lst):
        if item.id == obj.id:
            lst[i] = obj
            return
    lst.append(obj)


class DayService(BaseService):
    ctx: objects.DayContext | None
    date: datetime.date
    _observers: list[Callable[[str], Awaitable[None]]]

    def __init__(self, date: datetime.date) -> None:
        self.ctx = None
        self.date = date
        self._observers = []
        for repo in (event_repo, message_repo, task_repo):
            repo.register_observer(self.on_change)

    async def on_change(self, change: str, obj: T) -> None:
        if obj.date != self.date:
            return

        ctx: objects.DayContext = await self.get_context()
        if change == "delete":
            if isinstance(obj, objects.Event):
                ctx.events = [e for e in ctx.events if e.id != obj.id]
            elif isinstance(obj, objects.Task):
                ctx.tasks = [e for e in ctx.tasks if e.id != obj.id]
            elif isinstance(obj, objects.Message):
                ctx.messages = [e for e in ctx.messages if e.id != obj.id]
        elif change == "put":
            if isinstance(obj, objects.Event):
                replace(ctx.events, cast("objects.Event", obj))
            elif isinstance(obj, objects.Task):
                replace(ctx.tasks, cast("objects.Task", obj))
            elif isinstance(obj, objects.Message):
                replace(ctx.messages, cast("objects.Message", obj))

        await asyncio.gather(*(observer("update") for observer in self._observers))

    async def get_context(self) -> objects.DayContext:
        if self.ctx:
            if self.ctx.day.date == self.date:
                return self.ctx

        self.ctx = await self.load_context()
        return self.ctx

    async def set_date(self, date: datetime.date) -> None:
        if self.date != date:
            self.date = date
            self.ctx = await self.load_context()

    async def schedule(
        self,
    ) -> objects.DayContext:
        date: datetime.date = self.date
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

        return await self.load_context()

    async def load_context(
        self,
        schedule_routines: bool = True,
    ) -> objects.DayContext:
        tasks: list[objects.Task]
        events: list[objects.Event]
        messages: list[objects.Message]
        day: objects.Day

        date: datetime.date = self.date

        try:
            tasks, events, messages, day = await asyncio.gather(
                task_repo.search(date),
                event_repo.search(date),
                message_repo.search(date),
                day_repo.get(str(date)),
            )
        except exceptions.NotFoundError:
            return await self.schedule()

        if schedule_routines and not tasks:
            tasks = await routine_svc.schedule(date)

        return objects.DayContext(
            day=day,
            tasks=tasks,
            events=events,
            messages=messages,
        )
