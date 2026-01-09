"""Queries to get upcoming tasks and calendar entries."""

from datetime import date, timedelta
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import (
    CalendarEntryRepositoryReadOnlyProtocol,
    TaskRepositoryReadOnlyProtocol,
)
from lykke.application.unit_of_work import ReadOnlyRepositories
from lykke.core.utils import filter_upcoming_calendar_entries, filter_upcoming_tasks
from lykke.core.constants import DEFAULT_LOOK_AHEAD
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntryEntity, TaskEntity, UserEntity


class GetUpcomingTasksHandler(BaseQueryHandler):
    """Gets tasks that are upcoming within a look-ahead window."""

    task_ro_repo: TaskRepositoryReadOnlyProtocol

    def __init__(self, ro_repos: ReadOnlyRepositories, user_id: UUID) -> None:
        super().__init__(ro_repos, user_id)

    async def get_upcoming_tasks(
        self, user: UserEntity, date: date, look_ahead: timedelta = DEFAULT_LOOK_AHEAD
    ) -> list[TaskEntity]:
        """Get tasks that are upcoming within the look-ahead window.

        Args:
            user: The user entity
            date: The date to start from
            look_ahead: The look-ahead window

        Returns:
            List of tasks that are upcoming within the look-ahead window
        """
        tasks = await self.task_ro_repo.search(value_objects.TaskQuery(date=date))
        return filter_upcoming_tasks(tasks, look_ahead)


class GetUpcomingCalendarEntriesHandler(BaseQueryHandler):
    """Gets calendar entries that are upcoming within a look-ahead window."""

    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol

    def __init__(self, ro_repos: ReadOnlyRepositories, user_id: UUID) -> None:
        super().__init__(ro_repos, user_id)

    async def get_upcoming_calendar_entries(
        self, user: UserEntity, date: date, look_ahead: timedelta = DEFAULT_LOOK_AHEAD
    ) -> list[CalendarEntryEntity]:
        """Get calendar entries that are upcoming within the look-ahead window.

        Args:
            user: The user entity
            date: The date to start from
            look_ahead: The look-ahead window

        Returns:
            List of calendar entries that are upcoming within the look-ahead window
        """
        calendar_entries = await self.calendar_entry_ro_repo.search(
            value_objects.CalendarEntryQuery(date=date)
        )
        return filter_upcoming_calendar_entries(calendar_entries, look_ahead)

