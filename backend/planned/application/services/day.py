import datetime
from typing import TypeVar
from uuid import UUID

from blinker import Signal

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.application.utils import filter_upcoming_events, filter_upcoming_tasks
from planned.core.constants import DEFAULT_LOOK_AHEAD
from planned.core.exceptions import exceptions
from planned.domain import entities as objects
from planned.domain.entities import User
from planned.domain.value_objects.repository_event import RepositoryEvent

from .base import BaseService
from .day_context_loader import DayContextLoader

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
    """Service for managing day context and operations."""

    ctx: objects.DayContext
    date: datetime.date
    signal_source: Signal
    uow_factory: UnitOfWorkFactory

    def __init__(
        self,
        user: User,
        ctx: objects.DayContext,
        uow_factory: UnitOfWorkFactory,
    ) -> None:
        """Initialize DayService.

        Args:
            user: The user for this service
            ctx: The day context to manage
            uow_factory: Factory for creating UnitOfWork instances
        """
        super().__init__(user)
        self.ctx = ctx
        self.date = ctx.day.date
        self.signal_source = Signal()
        self.uow_factory = uow_factory

        # Set up listeners for repository events
        # Access repository classes directly for signals (signals are class-level)
        from planned.infrastructure.repositories import (
            EventRepository,
            MessageRepository,
            TaskRepository,
        )

        EventRepository.signal_source.connect(self.on_event_change)
        MessageRepository.signal_source.connect(self.on_message_change)
        TaskRepository.signal_source.connect(self.on_task_change)

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
    ) -> None:
        """Set the date for this service and reload context.

        Args:
            date: The new date
            user_id: Optional user ID (defaults to self.user.id)
        """
        if self.date != date:
            self.date = date
            user_id = user_id or self.user.id
            self.ctx = await self.load_context(date=date, user_id=user_id)

    async def load_context(
        self,
        date: datetime.date | None = None,
        user_id: UUID | None = None,
    ) -> objects.DayContext:
        """Load complete day context for the current or specified date.

        Args:
            date: Optional date to load (defaults to self.date)
            user_id: Optional user ID (defaults to self.user.id)

        Returns:
            A DayContext with day, tasks, events, and messages loaded
        """
        date = date or self.date
        user_id = user_id or self.user.id

        uow = self.uow_factory.create(user_id)
        async with uow:
            # Create loader and load context
            loader = DayContextLoader(
                user=self.user,
                day_repo=uow.days,
                day_template_repo=uow.day_templates,
                event_repo=uow.events,
                message_repo=uow.messages,
                task_repo=uow.tasks,
            )

            self.ctx = await loader.load(date, user_id)
        return self.ctx

    async def get_or_preview(
        self,
        date: datetime.date,
    ) -> objects.Day:
        """Get an existing day or return a preview (unsaved) day.

        Args:
            date: The date to get or preview

        Returns:
            An existing Day if found, otherwise a preview Day (not saved)
        """
        uow = self.uow_factory.create(self.user.id)
        async with uow:
            day_id = objects.Day.id_from_date_and_user(date, self.user.id)
            try:
                return await uow.days.get(day_id)
            except exceptions.NotFoundError:
                # Day doesn't exist, create a preview
                user = await uow.users.get(self.user.id)
                template_slug = user.settings.template_defaults[date.weekday()]
                template = await uow.day_templates.get_by_slug(template_slug)
                return objects.Day.create_for_date(
                    date,
                    user_id=self.user.id,
                    template=template,
                )

    async def get_or_create(
        self,
        date: datetime.date,
    ) -> objects.Day:
        """Get an existing day or create a new one.

        Args:
            date: The date to get or create

        Returns:
            An existing Day if found, otherwise a newly created and saved Day
        """
        uow = self.uow_factory.create(self.user.id)
        async with uow:
            day_id = objects.Day.id_from_date_and_user(date, self.user.id)
            try:
                return await uow.days.get(day_id)
            except exceptions.NotFoundError:
                # Day doesn't exist, create it
                user = await uow.users.get(self.user.id)
                template_slug = user.settings.template_defaults[date.weekday()]
                template = await uow.day_templates.get_by_slug(template_slug)
                day = objects.Day.create_for_date(
                    date,
                    user_id=self.user.id,
                    template=template,
                )
                result = await uow.days.put(day)
                await uow.commit()
                return result

    async def save(self) -> None:
        """Save the current day context's day to the database."""
        uow = self.uow_factory.create(self.user.id)
        async with uow:
            await uow.days.put(self.ctx.day)
            await uow.commit()

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
