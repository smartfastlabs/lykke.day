"""Query to get a calendar by ID."""

from uuid import UUID

from planned.application.unit_of_work import ReadOnlyRepositories
from planned.domain.entities import CalendarEntity


class GetCalendarHandler:
    """Retrieves a single calendar by ID."""

    def __init__(self, ro_repos: ReadOnlyRepositories) -> None:
        self._ro_repos = ro_repos

    async def run(self, user_id: UUID, calendar_id: UUID) -> CalendarEntity:
        """Get a single calendar by ID.

        Args:
            user_id: The user making the request
            calendar_id: The ID of the calendar to retrieve

        Returns:
            The calendar entity

        Raises:
            NotFoundError: If calendar not found
        """
        return await self._ro_repos.calendar_ro_repo.get(calendar_id)

