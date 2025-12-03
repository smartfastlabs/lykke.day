import asyncio
import datetime
from collections.abc import Awaitable, Callable
from typing import Protocol, TypeVar, cast

from blinker import Signal

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
    ctx: objects.DayContext
    date: datetime.date
    signal_source: Signal

    def __init__(
        self,
        ctx: objects.DayContext,
    ) -> None:
        self.ctx = ctx
        self.date = ctx.day.date
        self.signal_source = Signal()

        for repo in (event_repo, message_repo, task_repo):
            repo.signal_source.connect(self.on_change)

    @classmethod
    async def for_date(cls, date: datetime.date) -> "DayService":
        return cls(ctx=await cls._load_context(date))

    async def on_change(self, change: str, obj: T) -> None:
        if obj.date != self.date:
            return

        if change == "delete":
            if isinstance(obj, objects.Event):
                self.ctx.events = [e for e in self.ctx.events if e.id != obj.id]
            elif isinstance(obj, objects.Task):
                self.ctx.tasks = [e for e in self.ctx.tasks if e.id != obj.id]
            elif isinstance(obj, objects.Message):
                self.ctx.messages = [e for e in self.ctx.messages if e.id != obj.id]
        elif change == "put":
            if isinstance(obj, objects.Event):
                replace(self.ctx.events, cast("objects.Event", obj))
            elif isinstance(obj, objects.Task):
                replace(self.ctx.tasks, cast("objects.Task", obj))
            elif isinstance(obj, objects.Message):
                replace(self.ctx.messages, cast("objects.Message", obj))

        await self.signal_source.send_async(change, obj=obj)

    async def set_date(self, date: datetime.date) -> None:
        if self.date != date:
            self.date = date
            self.ctx = await self.load_context()

    async def start(self, template: str = "default") -> None:
        # confirm it is scheduled and do any all the things for the template
        # set the status, etc.
        pass

    async def end(self) -> None:
        pass

    async def schedule(
        self,
    ) -> objects.DayContext:
        return await self._schedule(self.date)

    @classmethod
    async def _schedule(
        cls,
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
            ),
        )

        return await cls._load_context(date)

    async def load_context(
        self,
        schedule_routines: bool = True,
    ) -> objects.DayContext:
        self.ctx = await self._load_context(
            self.date,
            schedule_routines=schedule_routines,
        )
        return self.ctx

    @classmethod
    async def _load_context(
        cls,
        date: datetime.date,
        schedule_routines: bool = True,
    ) -> objects.DayContext:
        tasks: list[objects.Task]
        events: list[objects.Event]
        messages: list[objects.Message]
        day: objects.Day

        try:
            tasks, events, messages, day = await asyncio.gather(
                task_repo.search(date),
                event_repo.search(date),
                message_repo.search(date),
                day_repo.get(str(date)),
            )
        except exceptions.NotFoundError:
            return await cls._schedule(date)

        if schedule_routines and not tasks:
            tasks = await routine_svc.schedule(date)

        return objects.DayContext(
            day=day,
            tasks=tasks,
            events=events,
            messages=messages,
        )
