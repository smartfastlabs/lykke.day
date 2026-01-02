"""DayService for managing day context and operations.

This service acts as a facade that delegates to command and query handlers.
It maintains backward compatibility while the codebase transitions to CQRS.
"""

import datetime
from uuid import UUID

from loguru import logger
from planned.application.commands.create_or_get_day import (
    CreateOrGetDayCommand,
    CreateOrGetDayHandler,
)
from planned.application.commands.save_day import SaveDayCommand, SaveDayHandler
from planned.application.queries.get_day_context import (
    GetDayContextHandler,
    GetDayContextQuery,
)
from planned.application.queries.get_upcoming_items import (
    GetUpcomingCalendarEntriesHandler,
    GetUpcomingCalendarEntriesQuery,
    GetUpcomingTasksHandler,
    GetUpcomingTasksQuery,
)
from planned.application.services.base import BaseService
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.core.constants import DEFAULT_LOOK_AHEAD
from planned.domain.entities import CalendarEntry, Day, DayContext, Task, User


class DayService(BaseService):
    """Stateless service for managing day context and operations.

    This service acts as a facade that delegates to command and query handlers.
    """

    date: datetime.date
    uow_factory: UnitOfWorkFactory
    _get_day_context_handler: GetDayContextHandler
    _get_upcoming_tasks_handler: GetUpcomingTasksHandler
    _get_upcoming_calendar_entries_handler: GetUpcomingCalendarEntriesHandler
    _create_or_get_day_handler: CreateOrGetDayHandler
    _save_day_handler: SaveDayHandler

    def __init__(
        self,
        user: User,
        date: datetime.date,
        uow_factory: UnitOfWorkFactory,
    ) -> None:
        """Initialize DayService.

        Args:
            user: The user for this service
            date: The date this service is for
            uow_factory: Factory for creating UnitOfWork instances
        """
        super().__init__(user)
        self.date = date
        self.uow_factory = uow_factory
        self._get_day_context_handler = GetDayContextHandler(uow_factory)
        self._get_upcoming_tasks_handler = GetUpcomingTasksHandler(uow_factory)
        self._get_upcoming_calendar_entries_handler = GetUpcomingCalendarEntriesHandler(
            uow_factory
        )
        self._create_or_get_day_handler = CreateOrGetDayHandler(uow_factory)
        self._save_day_handler = SaveDayHandler(uow_factory)
        logger.debug(f"DayService initialized for date {self.date}")

    async def load_context(
        self,
        date: datetime.date | None = None,
        user_id: UUID | None = None,
    ) -> DayContext:
        """Load complete day context for the current or specified date.

        Args:
            date: Optional date to load (defaults to self.date)
            user_id: Optional user ID (defaults to self.user.id)

        Returns:
            A DayContext with day, tasks, events, and messages loaded
        """
        date = date or self.date
        user_id = user_id or self.user.id

        query = GetDayContextQuery(user=self.user, date=date)
        return await self._get_day_context_handler.handle(query)

    async def get_or_preview(
        self,
        date: datetime.date,
    ) -> Day:
        """Get an existing day or return a preview (unsaved) day.

        Args:
            date: The date to get or preview

        Returns:
            An existing Day if found, otherwise a preview Day (not saved)
        """
        day_ctx = await self.load_context(date=date)
        return day_ctx.day

    async def get_or_create(
        self,
        date: datetime.date,
    ) -> Day:
        """Get an existing day or create a new one.

        Args:
            date: The date to get or create

        Returns:
            An existing Day if found, otherwise a newly created and saved Day
        """
        cmd = CreateOrGetDayCommand(user_id=self.user.id, date=date)
        return await self._create_or_get_day_handler.handle(cmd)

    async def save(self, day: Day) -> None:
        """Save a day to the database.

        Args:
            day: The day entity to save
        """
        cmd = SaveDayCommand(user_id=self.user.id, day=day)
        await self._save_day_handler.handle(cmd)

    async def get_upcoming_tasks(
        self,
        look_ahead: datetime.timedelta = DEFAULT_LOOK_AHEAD,
    ) -> list[Task]:
        """Get tasks that are upcoming within the look-ahead window.

        Args:
            look_ahead: The time window to look ahead

        Returns:
            List of tasks that are upcoming within the look-ahead window
        """
        query = GetUpcomingTasksQuery(
            user=self.user, date=self.date, look_ahead=look_ahead
        )
        return await self._get_upcoming_tasks_handler.handle(query)

    async def get_upcoming_calendar_entries(
        self,
        look_ahead: datetime.timedelta = DEFAULT_LOOK_AHEAD,
    ) -> list[CalendarEntry]:
        """Get calendar entries that are upcoming within the look-ahead window.

        Args:
            look_ahead: The time window to look ahead

        Returns:
            List of calendar entries that are upcoming within the look-ahead window
        """
        query = GetUpcomingCalendarEntriesQuery(
            user=self.user, date=self.date, look_ahead=look_ahead
        )
        return await self._get_upcoming_calendar_entries_handler.handle(query)
