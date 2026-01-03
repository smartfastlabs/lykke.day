"""Queries to get upcoming tasks and calendar entries."""

from datetime import date, timedelta

from planned.application.unit_of_work import ReadOnlyRepositories
from planned.core.utils import filter_upcoming_calendar_entries, filter_upcoming_tasks
from planned.core.constants import DEFAULT_LOOK_AHEAD
from planned.domain import value_objects
from planned.domain.entities import CalendarEntryEntity, TaskEntity, UserEntity


class GetUpcomingTasksHandler:
    """Gets tasks that are upcoming within a look-ahead window."""

    def __init__(self, ro_repos: ReadOnlyRepositories) -> None:
        self._ro_repos = ro_repos

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
        tasks = await self._ro_repos.task_ro_repo.search_query(value_objects.DateQuery(date=date))
        return filter_upcoming_tasks(tasks, look_ahead)


class GetUpcomingCalendarEntriesHandler:
    """Gets calendar entries that are upcoming within a look-ahead window."""

    def __init__(self, ro_repos: ReadOnlyRepositories) -> None:
        self._ro_repos = ro_repos

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
        calendar_entries = await self._ro_repos.calendar_entry_ro_repo.search_query(
            value_objects.DateQuery(date=date)
        )
        return filter_upcoming_calendar_entries(calendar_entries, look_ahead)

