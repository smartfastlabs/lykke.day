"""Query to get a calendar by ID."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import CalendarRepositoryReadOnlyProtocol
from lykke.domain.entities import CalendarEntity


@dataclass(frozen=True)
class GetCalendarQuery(Query):
    """Query to get a calendar by ID."""

    calendar_id: UUID


class GetCalendarHandler(BaseQueryHandler[GetCalendarQuery, CalendarEntity]):
    """Retrieves a single calendar by ID."""

    calendar_ro_repo: CalendarRepositoryReadOnlyProtocol

    async def handle(self, query: GetCalendarQuery) -> CalendarEntity:
        """Get a single calendar by ID.

        Args:
            query: The query containing the calendar ID

        Returns:
            The calendar entity

        Raises:
            NotFoundError: If calendar not found
        """
        return await self.calendar_ro_repo.get(query.calendar_id)
