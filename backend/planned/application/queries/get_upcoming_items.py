"""Queries to get upcoming tasks and calendar entries."""

from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from planned.application.queries.get_day_context import GetDayContextHandler, GetDayContextQuery
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.application.utils import filter_upcoming_calendar_entries, filter_upcoming_tasks
from planned.core.constants import DEFAULT_LOOK_AHEAD
from planned.domain import entities

from .base import Query, QueryHandler


@dataclass(frozen=True)
class GetUpcomingTasksQuery(Query):
    """Query to get tasks that are upcoming within a look-ahead window."""

    user: entities.User
    date: date
    look_ahead: timedelta = DEFAULT_LOOK_AHEAD


@dataclass(frozen=True)
class GetUpcomingCalendarEntriesQuery(Query):
    """Query to get calendar entries that are upcoming within a look-ahead window."""

    user: entities.User
    date: date
    look_ahead: timedelta = DEFAULT_LOOK_AHEAD


class GetUpcomingTasksHandler(QueryHandler[GetUpcomingTasksQuery, list[entities.Task]]):
    """Handles GetUpcomingTasksQuery."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory
        self._day_context_handler = GetDayContextHandler(uow_factory)

    async def handle(self, query: GetUpcomingTasksQuery) -> list[entities.Task]:
        """Get tasks that are upcoming within the look-ahead window.

        Args:
            query: The query containing user, date, and look_ahead

        Returns:
            List of tasks that are upcoming within the look-ahead window
        """
        day_context_query = GetDayContextQuery(user=query.user, date=query.date)
        day_ctx = await self._day_context_handler.handle(day_context_query)
        return filter_upcoming_tasks(day_ctx.tasks, query.look_ahead)


class GetUpcomingCalendarEntriesHandler(
    QueryHandler[GetUpcomingCalendarEntriesQuery, list[entities.CalendarEntry]]
):
    """Handles GetUpcomingCalendarEntriesQuery."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory
        self._day_context_handler = GetDayContextHandler(uow_factory)

    async def handle(
        self, query: GetUpcomingCalendarEntriesQuery
    ) -> list[entities.CalendarEntry]:
        """Get calendar entries that are upcoming within the look-ahead window.

        Args:
            query: The query containing user, date, and look_ahead

        Returns:
            List of calendar entries that are upcoming within the look-ahead window
        """
        day_context_query = GetDayContextQuery(user=query.user, date=query.date)
        day_ctx = await self._day_context_handler.handle(day_context_query)
        return filter_upcoming_calendar_entries(day_ctx.calendar_entries, query.look_ahead)

