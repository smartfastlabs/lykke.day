"""Query to get a calendar entry series by ID."""

from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import (
    CalendarEntrySeriesRepositoryReadOnlyProtocol,
)
from lykke.domain.entities import CalendarEntrySeriesEntity


class GetCalendarEntrySeriesHandler(BaseQueryHandler):
    """Retrieve a single calendar entry series by ID."""

    calendar_entry_series_ro_repo: CalendarEntrySeriesRepositoryReadOnlyProtocol

    async def run(self, series_id: UUID) -> CalendarEntrySeriesEntity:
        """Get a calendar entry series by ID."""
        return await self.calendar_entry_series_ro_repo.get(series_id)


