"""Queries to get upcoming tasks and calendar entries."""

from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.core.utils import filter_upcoming_calendar_entries, filter_upcoming_tasks
from planned.core.constants import DEFAULT_LOOK_AHEAD
from planned.core.exceptions import NotFoundError
from planned.domain import value_objects
from planned.domain.entities import CalendarEntity, CalendarEntryEntity, TaskEntity, UserEntity

from .base import Query, QueryHandler


@dataclass(frozen=True)
class GetUpcomingTasksQuery(Query):
    """Query to get tasks that are upcoming within a look-ahead window."""

    user: UserEntity
    date: date
    look_ahead: timedelta = DEFAULT_LOOK_AHEAD


@dataclass(frozen=True)
class GetUpcomingCalendarEntriesQuery(Query):
    """Query to get calendar entries that are upcoming within a look-ahead window."""

    user: UserEntity
    date: date
    look_ahead: timedelta = DEFAULT_LOOK_AHEAD


class GetUpcomingTasksHandler(QueryHandler[GetUpcomingTasksQuery, list[TaskEntity]]):
    """Handles GetUpcomingTasksQuery."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def handle(self, query: GetUpcomingTasksQuery) -> list[TaskEntity]:
        """Get tasks that are upcoming within the look-ahead window.

        Args:
            query: The query containing user, date, and look_ahead

        Returns:
            List of tasks that are upcoming within the look-ahead window
        """
        async with self._uow_factory.create(query.user.id) as uow:
            tasks = await uow.tasks.search_query(value_objects.DateQuery(date=query.date))
            return filter_upcoming_tasks(tasks, query.look_ahead)


class GetUpcomingCalendarEntriesHandler(
    QueryHandler[GetUpcomingCalendarEntriesQuery, list[CalendarEntryEntity]]
):
    """Handles GetUpcomingCalendarEntriesQuery."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def handle(
        self, query: GetUpcomingCalendarEntriesQuery
    ) -> list[CalendarEntryEntity]:
        """Get calendar entries that are upcoming within the look-ahead window.

        Args:
            query: The query containing user, date, and look_ahead

        Returns:
            List of calendar entries that are upcoming within the look-ahead window
        """
        async with self._uow_factory.create(query.user.id) as uow:
            calendar_entries = await uow.calendar_entries.search_query(
                value_objects.DateQuery(date=query.date)
            )
            return filter_upcoming_calendar_entries(calendar_entries, query.look_ahead)

