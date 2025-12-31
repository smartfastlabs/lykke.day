import asyncio
import datetime
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
from planned.application.utils import filter_upcoming_events, filter_upcoming_tasks
from planned.core.constants import DEFAULT_END_OF_DAY_TIME, DEFAULT_LOOK_AHEAD
from planned.core.exceptions import exceptions
from planned.domain import entities as objects
from planned.domain.entities import User
from planned.domain.value_objects.query import DateQuery
from planned.domain.value_objects.repository_event import RepositoryEvent

from .base import BaseService

T = TypeVar("T")


def replace(lst: list[T], obj: T) -> None:
    """Replace an object in a list by id, or append if not found."""
    # All objects passed here have id attribute (Event, Task, Message)
    for i, item in enumerate(lst):
        if getattr(item, "id", None) == getattr(obj, "id", None):
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
        user: User,
        ctx: objects.DayContext,
        day_repo: DayRepositoryProtocol,
        day_template_repo: DayTemplateRepositoryProtocol,
        event_repo: EventRepositoryProtocol,
        message_repo: MessageRepositoryProtocol,
        task_repo: TaskRepositoryProtocol,
    ) -> None:
        super().__init__(user)
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

    async def on_event_change(
        self, _sender: object | None = None, *, event: RepositoryEvent[objects.Event]
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
        self, _sender: object | None = None, *, event: RepositoryEvent[objects.Message]
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
        self, _sender: object | None = None, *, event: RepositoryEvent[objects.Task]
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

    async def set_date(
        self,
        date: datetime.date,
        user_id: UUID | None = None,
        user_repo: UserRepositoryProtocol | None = None,
    ) -> None:
        if self.date != date:
            self.date = date
            # Extract user_id from repository if not provided
            if user_id is None:
                # Try to get from repository (repositories store user_id)
                if hasattr(self.day_repo, "user_id"):
                    user_id = self.day_repo.user_id
                else:
                    raise ValueError("user_id required for set_date")
            self.ctx = await self.load_context(
                date=date,
                user_id=user_id,
                user_repo=user_repo,
            )

    async def load_context(
        self,
        date: datetime.date | None = None,
        user_id: UUID | None = None,
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

        # Extract user_id from repository if not provided
        if user_id is None:
            if hasattr(self.day_repo, "user_id"):
                user_id = self.day_repo.user_id
            else:
                raise ValueError("user_id required for load_context")

        tasks: list[objects.Task] = []
        events: list[objects.Event] = []
        messages: list[objects.Message] = []
        day: objects.Day

        try:
            day_id = objects.Day.id_from_date_and_user(date, user_id)
            tasks, events, messages, day = await asyncio.gather(
                task_repo.search_query(DateQuery(date=date)),
                event_repo.search_query(DateQuery(date=date)),
                message_repo.search_query(DateQuery(date=date)),
                day_repo.get(day_id),
            )
        except exceptions.NotFoundError:
            template_slug = self.user.settings.template_defaults[date.weekday()]
            template = await day_template_repo.get_by_slug(template_slug)
            day = await type(self).base_day(
                date,
                user_id=user_id,
                template=template,
            )

        self.ctx = objects.DayContext(
            day=day,
            tasks=sorted(
                tasks,
                key=lambda x: x.schedule.start_time
                if x.schedule and x.schedule.start_time
                else DEFAULT_END_OF_DAY_TIME,
            ),
            events=sorted(events, key=lambda e: e.starts_at),
            messages=messages,
        )
        return self.ctx

    @classmethod
    async def base_day(
        cls,
        date: datetime.date,
        user_id: UUID,
        template: objects.DayTemplate,
    ) -> objects.Day:
        return objects.Day(
            user_id=user_id,
            date=date,
            status=objects.DayStatus.UNSCHEDULED,
            template=template,
            alarm=template.alarm,
        )

    async def get_or_preview(
        self,
        date: datetime.date,
        user: User,
        user_repo: UserRepositoryProtocol,
    ) -> objects.Day:
        """Get an existing day or return a preview (unsaved) day.

        Args:
            date: The date to get or preview
            user: The user for the day
            user_repo: Repository for user lookups

        Returns:
            An existing Day if found, otherwise a preview Day (not saved)
        """
        day_id = objects.Day.id_from_date_and_user(date, user.id)
        try:
            return await self.day_repo.get(day_id)
        except exceptions.NotFoundError:
            # Day doesn't exist, create a preview
            template_slug = user.settings.template_defaults[date.weekday()]
            template = await self.day_template_repo.get_by_slug(template_slug)
            return await type(self).base_day(
                date,
                user_id=user.id,
                template=template,
            )

    async def get_or_create(
        self,
        date: datetime.date,
        user: User,
        user_repo: UserRepositoryProtocol,
    ) -> objects.Day:
        """Get an existing day or create a new one.

        Args:
            date: The date to get or create
            user: The user for the day
            user_repo: Repository for user lookups

        Returns:
            An existing Day if found, otherwise a newly created and saved Day
        """
        day_id = objects.Day.id_from_date_and_user(date, user.id)
        try:
            return await self.day_repo.get(day_id)
        except exceptions.NotFoundError:
            # Day doesn't exist, create it
            template_slug = user.settings.template_defaults[date.weekday()]
            template = await self.day_template_repo.get_by_slug(template_slug)
            return await self.day_repo.put(
                await type(self).base_day(
                    date,
                    user_id=user.id,
                    template=template,
                )
            )

    async def save(self) -> None:
        await self.day_repo.put(self.ctx.day)

    async def get_upcoming_tasks(
        self,
        look_ahead: datetime.timedelta = DEFAULT_LOOK_AHEAD,
    ) -> list[objects.Task]:
        """Get tasks that are upcoming within the look-ahead window.

        Args:
            look_ahead: The time window to look ahead

        Returns:
            List of tasks that are upcoming within the look-ahead window
        """
        return filter_upcoming_tasks(self.ctx.tasks, look_ahead)

    async def get_upcoming_events(
        self,
        look_ahead: datetime.timedelta = DEFAULT_LOOK_AHEAD,
    ) -> list[objects.Event]:
        """Get events that are upcoming within the look-ahead window.

        Args:
            look_ahead: The time window to look ahead

        Returns:
            List of events that are upcoming within the look-ahead window
        """
        return filter_upcoming_events(self.ctx.events, look_ahead)
