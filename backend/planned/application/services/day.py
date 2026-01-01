import datetime
from uuid import UUID

from loguru import logger
from planned.application.events import domain_event_signal
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.application.utils import (
    filter_upcoming_calendar_entries,
    filter_upcoming_tasks,
)
from planned.core.constants import DEFAULT_END_OF_DAY_TIME, DEFAULT_LOOK_AHEAD
from planned.core.exceptions import NotFoundError
from planned.domain import entities as objects
from planned.domain.entities import User
from planned.domain.events.base import DomainEvent
from planned.domain.events.day_events import (
    DayCompletedEvent,
    DayScheduledEvent,
    DayUnscheduledEvent,
)
from planned.domain.events.task_events import (
    TaskActionRecordedEvent,
    TaskCompletedEvent,
    TaskStatusChangedEvent,
)

from .base import BaseService
from .day_context_loader import DayContextLoader


class DayService(BaseService):
    """Service for managing day context and operations.

    Subscribes to domain events to keep its cache (ctx) up to date.
    """

    ctx: objects.DayContext
    date: datetime.date
    uow_factory: UnitOfWorkFactory
    _is_subscribed: bool

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
        self.uow_factory = uow_factory
        self._is_subscribed = False

    def subscribe_to_events(self) -> None:
        """Subscribe to domain events to keep cache up to date."""
        if self._is_subscribed:
            return
        domain_event_signal.connect(self._handle_domain_event)
        self._is_subscribed = True
        logger.debug(f"DayService subscribed to domain events for date {self.date}")

    def unsubscribe_from_events(self) -> None:
        """Unsubscribe from domain events."""
        if not self._is_subscribed:
            return
        domain_event_signal.disconnect(self._handle_domain_event)
        self._is_subscribed = False
        logger.debug(f"DayService unsubscribed from domain events for date {self.date}")

    async def _handle_domain_event(
        self,
        sender: type[DomainEvent],
        event: DomainEvent,
    ) -> None:
        """Handle incoming domain events and update cache accordingly.

        Args:
            sender: The event class (used by blinker for filtering)
            event: The domain event to handle
        """
        # Task events
        if isinstance(event, TaskStatusChangedEvent | TaskCompletedEvent):
            await self._handle_task_status_change(event)
        elif isinstance(event, TaskActionRecordedEvent):
            await self._handle_task_action_recorded(event)
        # Day events
        elif isinstance(event, DayScheduledEvent | DayCompletedEvent):
            await self._handle_day_status_change(event)
        elif isinstance(event, DayUnscheduledEvent):
            await self._handle_day_unscheduled(event)

    async def _handle_task_status_change(
        self,
        event: TaskStatusChangedEvent | TaskCompletedEvent,
    ) -> None:
        """Handle task status change by reloading the task from the database.

        Args:
            event: The task status change event
        """
        task_id = event.task_id

        # Check if this task is in our context
        task_in_ctx = next((t for t in self.ctx.tasks if t.id == task_id), None)
        if task_in_ctx is None:
            # Task not in our day's context, ignore
            return

        # Reload the task from database to get updated state
        uow = self.uow_factory.create(self.user.id)
        async with uow:
            try:
                updated_task = await uow.tasks.get(task_id)
                # Update the task in our context
                self._update_task_in_context(updated_task)
                logger.debug(f"Updated task {task_id} in DayService cache")
            except NotFoundError:
                # Task was deleted, remove from context
                self._remove_task_from_context(task_id)
                logger.debug(f"Removed deleted task {task_id} from DayService cache")

    async def _handle_task_action_recorded(
        self,
        event: TaskActionRecordedEvent,
    ) -> None:
        """Handle task action recorded by reloading the task.

        Args:
            event: The task action recorded event
        """
        task_id = event.task_id

        # Check if this task is in our context
        task_in_ctx = next((t for t in self.ctx.tasks if t.id == task_id), None)
        if task_in_ctx is None:
            return

        # Reload the task from database
        uow = self.uow_factory.create(self.user.id)
        async with uow:
            try:
                updated_task = await uow.tasks.get(task_id)
                self._update_task_in_context(updated_task)
                logger.debug(f"Updated task {task_id} after action in DayService cache")
            except NotFoundError:
                self._remove_task_from_context(task_id)

    async def _handle_day_status_change(
        self,
        event: DayScheduledEvent | DayCompletedEvent,
    ) -> None:
        """Handle day status change by reloading the day.

        Args:
            event: The day status change event
        """
        # Only handle events for our day
        if event.date != self.date:
            return

        # Reload the day from database
        uow = self.uow_factory.create(self.user.id)
        async with uow:
            try:
                updated_day = await uow.days.get(event.day_id)
                self.ctx.day = updated_day
                logger.debug(f"Updated day {event.day_id} in DayService cache")
            except NotFoundError:
                logger.warning(f"Day {event.day_id} not found after status change")

    async def _handle_day_unscheduled(self, event: DayUnscheduledEvent) -> None:
        """Handle day unscheduled event.

        Args:
            event: The day unscheduled event
        """
        if event.date != self.date:
            return

        # Reload the day from database
        uow = self.uow_factory.create(self.user.id)
        async with uow:
            try:
                updated_day = await uow.days.get(event.day_id)
                self.ctx.day = updated_day
                logger.debug(f"Updated unscheduled day {event.day_id} in cache")
            except NotFoundError:
                logger.warning(f"Day {event.day_id} not found after unschedule")

    def _update_task_in_context(self, updated_task: objects.Task) -> None:
        """Update a task in the context, maintaining sort order.

        Args:
            updated_task: The updated task to put in the context
        """
        # Remove old version and add updated one
        self.ctx.tasks = [t for t in self.ctx.tasks if t.id != updated_task.id]
        self.ctx.tasks.append(updated_task)
        # Re-sort by start time
        self.ctx.tasks.sort(
            key=lambda x: x.schedule.start_time
            if x.schedule and x.schedule.start_time
            else DEFAULT_END_OF_DAY_TIME,
        )

    def _remove_task_from_context(self, task_id: UUID) -> None:
        """Remove a task from the context.

        Args:
            task_id: The ID of the task to remove
        """
        self.ctx.tasks = [t for t in self.ctx.tasks if t.id != task_id]

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
                calendar_entry_repo=uow.calendar_entries,
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
            except NotFoundError:
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
            except NotFoundError:
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

    async def get_upcoming_calendar_entries(
        self,
        look_ahead: datetime.timedelta = DEFAULT_LOOK_AHEAD,
    ) -> list[objects.CalendarEntry]:
        """Get calendar entries that are upcoming within the look-ahead window.

        Args:
            look_ahead: The time window to look ahead

        Returns:
            List of calendar entries that are upcoming within the look-ahead window
        """
        return filter_upcoming_calendar_entries(self.ctx.calendar_entries, look_ahead)
