import asyncio
import datetime
from contextlib import suppress
from typing import Protocol, TypeVar

from blinker import Signal

from planned.application.repositories import (
    DayRepositoryProtocol,
    DayTemplateRepositoryProtocol,
    EventRepositoryProtocol,
    MessageRepositoryProtocol,
    TaskRepositoryProtocol,
)
from planned.core.exceptions import exceptions
from planned.domain import entities as objects
from planned.infrastructure.repositories.base.repository import ChangeEvent
from planned.infrastructure.utils.user_settings import load_user_settings
from planned.infrastructure.utils.dates import get_current_datetime, get_current_time
from planned.infrastructure.utils.decorators import hybridmethod

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
    day_repo: DayRepositoryProtocol
    day_template_repo: DayTemplateRepositoryProtocol
    event_repo: EventRepositoryProtocol
    message_repo: MessageRepositoryProtocol
    task_repo: TaskRepositoryProtocol

    def __init__(
        self,
        ctx: objects.DayContext,
        day_repo: DayRepositoryProtocol,
        day_template_repo: DayTemplateRepositoryProtocol,
        event_repo: EventRepositoryProtocol,
        message_repo: MessageRepositoryProtocol,
        task_repo: TaskRepositoryProtocol,
    ) -> None:
        self.ctx = ctx
        self.date = ctx.day.date
        self.signal_source = Signal()
        self.day_repo = day_repo
        self.day_template_repo = day_template_repo
        self.event_repo = event_repo
        self.message_repo = message_repo
        self.task_repo = task_repo

        self.event_repo.listen(self.on_event_change)
        self.message_repo.listen(self.on_message_change)
        self.task_repo.listen(self.on_task_change)

    @classmethod
    async def for_date(
        cls,
        date: datetime.date,
        day_repo: DayRepositoryProtocol,
        day_template_repo: DayTemplateRepositoryProtocol,
        event_repo: EventRepositoryProtocol,
        message_repo: MessageRepositoryProtocol,
        task_repo: TaskRepositoryProtocol,
    ) -> "DayService":
        ctx = await cls.load_context(
            date,
            day_repo=day_repo,
            day_template_repo=day_template_repo,
            event_repo=event_repo,
            message_repo=message_repo,
            task_repo=task_repo,
        )
        return cls(
            ctx=ctx,
            day_repo=day_repo,
            day_template_repo=day_template_repo,
            event_repo=event_repo,
            message_repo=message_repo,
            task_repo=task_repo,
        )

    async def on_event_change(
        self, _sender: object | None = None, *, event: ChangeEvent[objects.Event]
    ) -> None:
        obj = event.value
        change = event.type

        if obj.date != self.date:
            return

        if change == "delete":
            self.ctx.events = [e for e in self.ctx.events if e.id != obj.id]
        elif change in ("create", "update"):
            replace(self.ctx.events, obj)

        await self.signal_source.send_async("change", event=event)

    async def on_message_change(
        self, _sender: object | None = None, *, event: ChangeEvent[objects.Message]
    ) -> None:
        obj = event.value
        change = event.type

        if obj.date != self.date:
            return

        if change == "delete":
            self.ctx.messages = [m for m in self.ctx.messages if m.id != obj.id]
        elif change in ("create", "update"):
            replace(self.ctx.messages, obj)

        await self.signal_source.send_async("change", event=event)

    async def on_task_change(
        self, _sender: object | None = None, *, event: ChangeEvent[objects.Task]
    ) -> None:
        obj = event.value
        change = event.type

        if obj.date != self.date:
            return

        if change == "delete":
            self.ctx.tasks = [t for t in self.ctx.tasks if t.id != obj.id]
        elif change in ("create", "update"):
            replace(self.ctx.tasks, obj)

        await self.signal_source.send_async("change", event=event)

    async def set_date(self, date: datetime.date) -> None:
        if self.date != date:
            self.date = date
            self.ctx = await type(self).load_context(
                date,
                day_repo=self.day_repo,
                day_template_repo=self.day_template_repo,
                event_repo=self.event_repo,
                message_repo=self.message_repo,
                task_repo=self.task_repo,
            )

    @hybridmethod
    async def load_context(
        self,
        date: datetime.date | None = None,
        day_repo: DayRepositoryProtocol | None = None,
        day_template_repo: DayTemplateRepositoryProtocol | None = None,
        event_repo: EventRepositoryProtocol | None = None,
        message_repo: MessageRepositoryProtocol | None = None,
        task_repo: TaskRepositoryProtocol | None = None,
    ) -> objects.DayContext:
        # Use instance attributes if not provided
        date = date or self.date
        day_repo = day_repo or self.day_repo
        day_template_repo = day_template_repo or self.day_template_repo
        event_repo = event_repo or self.event_repo
        message_repo = message_repo or self.message_repo
        task_repo = task_repo or self.task_repo

        self.ctx = await type(self).load_context(
            date,
            day_repo=day_repo,
            day_template_repo=day_template_repo,
            event_repo=event_repo,
            message_repo=message_repo,
            task_repo=task_repo,
        )
        return self.ctx

    @load_context.classmethod
    async def load_context_cls(
        cls,  # noqa: N805
        date: datetime.date,
        day_repo: DayRepositoryProtocol,
        day_template_repo: DayTemplateRepositoryProtocol,
        event_repo: EventRepositoryProtocol,
        message_repo: MessageRepositoryProtocol,
        task_repo: TaskRepositoryProtocol,
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
            day = await cls.base_day(
                date,
                day_template_repo=day_template_repo,
            )

        return objects.DayContext(
            day=day,
            tasks=sorted(
                tasks,
                key=lambda x: x.schedule.start_time
                if x.schedule and x.schedule.start_time
                else datetime.time(23, 59),
            ),
            events=sorted(events, key=lambda e: e.starts_at),
            messages=messages,
        )

    @classmethod
    async def base_day(
        cls,
        date: datetime.date,
        day_template_repo: DayTemplateRepositoryProtocol,
        template_id: str | None = None,
    ) -> objects.Day:
        if template_id is None:
            user_settings = load_user_settings()
            template_id = user_settings.template_defaults[date.weekday()]

        template: objects.DayTemplate = await day_template_repo.get(template_id)

        return objects.Day(
            date=date,
            status=objects.DayStatus.UNSCHEDULED,
            template_id=template.id,
            alarm=template.alarm,
        )

    @classmethod
    async def get_or_preview(
        cls,
        date: datetime.date,
        day_repo: DayRepositoryProtocol,
        day_template_repo: DayTemplateRepositoryProtocol,
    ) -> objects.Day:
        with suppress(exceptions.NotFoundError):
            return await day_repo.get(str(date))

        return await cls.base_day(
            date,
            day_template_repo=day_template_repo,
        )

    @classmethod
    async def get_or_create(
        cls,
        date: datetime.date,
        day_repo: DayRepositoryProtocol,
        day_template_repo: DayTemplateRepositoryProtocol,
    ) -> objects.Day:
        with suppress(exceptions.NotFoundError):
            return await day_repo.get(str(date))

        return await day_repo.put(
            await cls.base_day(
                date,
                day_template_repo=day_template_repo,
            )
        )

    async def save(self) -> None:
        await self.day_repo.put(self.ctx.day)

    async def get_upcomming_tasks(
        self,
        look_ahead: datetime.timedelta = datetime.timedelta(minutes=30),
    ) -> list[objects.Task]:
        now: datetime.time = get_current_time()
        cutoff_time: datetime.time = (get_current_datetime() + look_ahead).time()

        if cutoff_time < get_current_time():
            # tomorrow
            return self.ctx.tasks

        result: list[objects.Task] = []
        for task in self.ctx.tasks:
            if (
                task.status
                not in (
                    objects.TaskStatus.PENDING,
                    objects.TaskStatus.NOT_STARTED,
                    objects.TaskStatus.READY,
                )
                or task.completed_at
                or not task.schedule
            ):
                continue

            if task.schedule.available_time:
                if task.schedule.available_time > now:
                    continue

            elif task.schedule.start_time and cutoff_time < task.schedule.start_time:
                continue

            if task.schedule.end_time and now > task.schedule.end_time:
                continue

            result.append(task)

        return result

    async def get_upcomming_events(
        self,
        look_ahead: datetime.timedelta = datetime.timedelta(minutes=30),
    ) -> list[objects.Event]:
        now: datetime.datetime = get_current_datetime()
        result: list[objects.Event] = []
        for event in self.ctx.events:
            if event.status == "cancelled":
                continue

            if event.starts_at < now:
                if event.ends_at and event.ends_at < now:
                    continue
            elif event.starts_at - now > look_ahead:
                continue

            result.append(event)

        return result
