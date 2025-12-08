import asyncio
import datetime
from contextlib import suppress
from typing import Protocol, TypeVar, cast

from blinker import Signal

from planned import exceptions, objects
from planned.objects.user_settings import user_settings
from planned.repositories import day_repo, event_repo, message_repo, task_repo
from planned.utils.decorators import hybridmethod

from .base import BaseService

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


_SERVICE_CACHE: dict[datetime.date, "DayService"] = {}


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

    def __new__(cls, ctx: objects.DayContext) -> "DayService":
        if ctx.day.date not in _SERVICE_CACHE:
            instance = super().__new__(cls)
            _SERVICE_CACHE[ctx.day.date] = instance
        return _SERVICE_CACHE[ctx.day.date]

    @classmethod
    async def for_date(cls, date: datetime.date) -> "DayService":
        return cls(ctx=await cls.load_context(date))

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

    @hybridmethod
    async def load_context(
        self,
    ) -> objects.DayContext:
        self.ctx = await type(self).load_context(
            self.date,
        )
        return self.ctx

    @load_context.classmethod
    async def load_context_cls(
        cls,  # noqa: N805
        date: datetime.date,
    ) -> objects.DayContext:
        tasks: list[objects.Task] = []
        events: list[objects.Event] = []
        messages: list[objects.Message] = []
        day: objects.Day

        try:
            tasks, events, messages, day = await asyncio.gather(
                task_repo.search(date),
                event_repo.search(date),
                message_repo.search(date),
                day_repo.get(str(date)),
            )
        except exceptions.NotFoundError:
            day = cls.base_day(date)

        return objects.DayContext(
            day=day,
            tasks=tasks,
            events=events,
            messages=messages,
        )

    @classmethod
    def base_day(
        cls,
        date: datetime.date,
        template: objects.DayTemplate | None = None,
    ) -> objects.Day:
        return objects.Day(
            date=date,
            status=objects.DayStatus.UNSCHEDULED,
            template_id=user_settings.template_defaults[date.weekday()],
            alarms=template.alarms if template else [],
        )

    @classmethod
    async def get_or_preview(cls, date: datetime.date) -> objects.Day:
        with suppress(exceptions.NotFoundError):
            return await day_repo.get(str(date))

        return cls.base_day(date)

    @classmethod
    async def get_or_create(cls, date: datetime.date) -> objects.Day:
        with suppress(exceptions.NotFoundError):
            return await day_repo.get(str(date))

        return await day_repo.put(cls.base_day(date))

    async def save(self) -> None:
        await day_repo.put(self.ctx.day)
