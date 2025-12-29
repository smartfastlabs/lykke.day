import asyncio
import datetime
from contextlib import suppress
from typing import TypeVar
from uuid import UUID

from blinker import Signal

from planned.application.repositories import (
    DayRepositoryProtocol,
    DayTemplateRepositoryProtocol,
    EventRepositoryProtocol,
    MessageRepositoryProtocol,
    TaskRepositoryProtocol,
    UserRepositoryProtocol,
)
from planned.core.exceptions import exceptions
from planned.domain import entities as objects
from planned.domain.value_objects.query import DateQuery
from planned.domain.value_objects.repository_event import RepositoryEvent
from planned.infrastructure.utils.dates import get_current_datetime, get_current_time
from planned.infrastructure.utils.decorators import hybridmethod

from .base import BaseService

T = TypeVar("T", bound=objects.BaseDateObject)


def replace(lst: list[T], obj: T) -> None:
    for i, item in enumerate(lst):
        if item.uuid == obj.uuid:
            lst[i] = obj
            return
    lst.append(obj)


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
        user_uuid: UUID,
        day_repo: DayRepositoryProtocol,
        day_template_repo: DayTemplateRepositoryProtocol,
        event_repo: EventRepositoryProtocol,
        message_repo: MessageRepositoryProtocol,
        task_repo: TaskRepositoryProtocol,
        user_repo: UserRepositoryProtocol | None = None,
    ) -> "DayService":
        ctx = await cls.load_context_cls(
            date,
            user_uuid=user_uuid,
            day_repo=day_repo,
            day_template_repo=day_template_repo,
            event_repo=event_repo,
            message_repo=message_repo,
            task_repo=task_repo,
            user_repo=user_repo,
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
        self, _sender: object | None = None, *, event: RepositoryEvent[objects.Event]
    ) -> None:
        obj = event.value
        change = event.type

        if obj.date != self.date:
            return

        if change == "delete":
            self.ctx.events = [e for e in self.ctx.events if e.uuid != obj.uuid]
        elif change in ("create", "update"):
            replace(self.ctx.events, obj)

        await self.signal_source.send_async("change", event=event)

    async def on_message_change(
        self, _sender: object | None = None, *, event: RepositoryEvent[objects.Message]
    ) -> None:
        obj = event.value
        change = event.type

        if obj.date != self.date:
            return

        if change == "delete":
            self.ctx.messages = [m for m in self.ctx.messages if m.uuid != obj.uuid]
        elif change in ("create", "update"):
            replace(self.ctx.messages, obj)

        await self.signal_source.send_async("change", event=event)

    async def on_task_change(
        self, _sender: object | None = None, *, event: RepositoryEvent[objects.Task]
    ) -> None:
        obj = event.value
        change = event.type

        if obj.date != self.date:
            return

        if change == "delete":
            self.ctx.tasks = [t for t in self.ctx.tasks if t.uuid != obj.uuid]
        elif change in ("create", "update"):
            replace(self.ctx.tasks, obj)

        await self.signal_source.send_async("change", event=event)

    async def set_date(
        self,
        date: datetime.date,
        user_uuid: UUID | None = None,
        user_repo: UserRepositoryProtocol | None = None,
    ) -> None:
        if self.date != date:
            self.date = date
            # Extract user_uuid from repository if not provided
            if user_uuid is None:
                # Try to get from repository (repositories store user_uuid)
                if hasattr(self.day_repo, "user_uuid"):
                    user_uuid = self.day_repo.user_uuid
                else:
                    raise ValueError("user_uuid required for set_date")
            self.ctx = await type(self).load_context_cls(
                date,
                user_uuid=user_uuid,
                day_repo=self.day_repo,
                day_template_repo=self.day_template_repo,
                event_repo=self.event_repo,
                message_repo=self.message_repo,
                task_repo=self.task_repo,
                user_repo=user_repo,
            )

    @hybridmethod
    async def load_context(
        self,
        date: datetime.date | None = None,
        user_uuid: UUID | None = None,
        day_repo: DayRepositoryProtocol | None = None,
        day_template_repo: DayTemplateRepositoryProtocol | None = None,
        event_repo: EventRepositoryProtocol | None = None,
        message_repo: MessageRepositoryProtocol | None = None,
        task_repo: TaskRepositoryProtocol | None = None,
        user_repo: UserRepositoryProtocol | None = None,
    ) -> objects.DayContext:
        # Use instance attributes if not provided
        date = date or self.date
        day_repo = day_repo or self.day_repo
        day_template_repo = day_template_repo or self.day_template_repo
        event_repo = event_repo or self.event_repo
        message_repo = message_repo or self.message_repo
        task_repo = task_repo or self.task_repo

        # Extract user_uuid from repository if not provided
        if user_uuid is None:
            if hasattr(self.day_repo, "user_uuid"):
                user_uuid = self.day_repo.user_uuid
            else:
                raise ValueError("user_uuid required for load_context")

        self.ctx = await type(self).load_context_cls(
            date,
            user_uuid=user_uuid,
            day_repo=day_repo,
            day_template_repo=day_template_repo,
            event_repo=event_repo,
            message_repo=message_repo,
            task_repo=task_repo,
            user_repo=user_repo,
        )
        return self.ctx

    @load_context.classmethod
    async def load_context_cls(
        cls,  # noqa: N805
        date: datetime.date,
        user_uuid: UUID,
        day_repo: DayRepositoryProtocol,
        day_template_repo: DayTemplateRepositoryProtocol,
        event_repo: EventRepositoryProtocol,
        message_repo: MessageRepositoryProtocol,
        task_repo: TaskRepositoryProtocol,
        user_repo: UserRepositoryProtocol | None = None,
    ) -> objects.DayContext:
        tasks: list[objects.Task] = []
        events: list[objects.Event] = []
        messages: list[objects.Message] = []
        day: objects.Day

        try:
            day_uuid = objects.Day.uuid_from_date_and_user(date, user_uuid)
            tasks, events, messages, day = await asyncio.gather(
                task_repo.search_query(DateQuery(date=date)),
                event_repo.search_query(DateQuery(date=date)),
                message_repo.search_query(DateQuery(date=date)),
                day_repo.get(day_uuid),
            )
        except exceptions.NotFoundError:
            day = await cls.base_day(
                date,
                user_uuid=user_uuid,
                day_template_repo=day_template_repo,
                user_repo=user_repo,
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
        user_uuid: UUID,
        day_template_repo: DayTemplateRepositoryProtocol,
        user_repo: UserRepositoryProtocol | None = None,
        template_uuid: UUID | None = None,
    ) -> objects.Day:
        if template_uuid is None:
            if user_repo is None:
                raise ValueError("user_repo required when template_uuid is None")
            user = await user_repo.get(str(user_uuid))
            # template_defaults stores slugs
            template_slug = user.settings.template_defaults[date.weekday()]
            template: objects.DayTemplate = await day_template_repo.get_by_slug(
                template_slug
            )
        else:
            template: objects.DayTemplate = await day_template_repo.get(template_uuid)

        return objects.Day(
            user_uuid=user_uuid,
            date=date,
            status=objects.DayStatus.UNSCHEDULED,
            template_uuid=template.uuid,
            alarm=template.alarm,
        )

    @classmethod
    async def get_or_preview(
        cls,
        date: datetime.date,
        user_uuid: UUID,
        day_repo: DayRepositoryProtocol,
        day_template_repo: DayTemplateRepositoryProtocol,
        user_repo: UserRepositoryProtocol | None = None,
    ) -> objects.Day:
        with suppress(exceptions.NotFoundError):
            day_uuid = objects.Day.uuid_from_date_and_user(date, user_uuid)
            return await day_repo.get(day_uuid)

        return await cls.base_day(
            date,
            user_uuid=user_uuid,
            day_template_repo=day_template_repo,
            user_repo=user_repo,
        )

    @classmethod
    async def get_or_create(
        cls,
        date: datetime.date,
        user_uuid: UUID,
        day_repo: DayRepositoryProtocol,
        day_template_repo: DayTemplateRepositoryProtocol,
        user_repo: UserRepositoryProtocol | None = None,
    ) -> objects.Day:
        with suppress(exceptions.NotFoundError):
            day_uuid = objects.Day.uuid_from_date_and_user(date, user_uuid)
            return await day_repo.get(day_uuid)

        return await day_repo.put(
            await cls.base_day(
                date,
                user_uuid=user_uuid,
                day_template_repo=day_template_repo,
                user_repo=user_repo,
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
