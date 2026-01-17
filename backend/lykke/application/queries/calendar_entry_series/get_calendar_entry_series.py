"""Query to get a calendar entry series by ID."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import (
    CalendarEntrySeriesRepositoryReadOnlyProtocol,
)
from lykke.domain.entities import CalendarEntrySeriesEntity


@dataclass(frozen=True)
class GetCalendarEntrySeriesQuery(Query):
    """Query to get a calendar entry series by ID."""

    calendar_entry_series_id: UUID


class GetCalendarEntrySeriesHandler(BaseQueryHandler[GetCalendarEntrySeriesQuery, CalendarEntrySeriesEntity]):
    """Retrieve a single calendar entry series by ID."""

    calendar_entry_series_ro_repo: CalendarEntrySeriesRepositoryReadOnlyProtocol

    async def handle(self, query: GetCalendarEntrySeriesQuery) -> CalendarEntrySeriesEntity:
        """Get a calendar entry series by ID."""
        return await self.calendar_entry_series_ro_repo.get(query.calendar_entry_series_id)


