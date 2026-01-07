"""Query to get a calendar by ID."""

from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import CalendarRepositoryReadOnlyProtocol
from lykke.domain.entities import CalendarEntity


class GetCalendarHandler(BaseQueryHandler):
    """Retrieves a single calendar by ID."""

    calendar_ro_repo: CalendarRepositoryReadOnlyProtocol

    async def run(self, calendar_id: UUID) -> CalendarEntity:
        """Get a single calendar by ID.

        Args:
            calendar_id: The ID of the calendar to retrieve

        Returns:
            The calendar entity

        Raises:
            NotFoundError: If calendar not found
        """
        return await self.calendar_ro_repo.get(calendar_id)
