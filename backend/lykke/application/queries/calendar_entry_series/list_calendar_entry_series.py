"""Query to search calendar entry series with pagination."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import CalendarEntrySeriesRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntrySeriesEntity


@dataclass(frozen=True)
class SearchCalendarEntrySeriesQuery(Query):
    """Query to search calendar entry series."""

    search_query: value_objects.CalendarEntrySeriesQuery | None = None


class SearchCalendarEntrySeriesHandler(BaseQueryHandler[SearchCalendarEntrySeriesQuery, value_objects.PagedQueryResponse[CalendarEntrySeriesEntity]]):
    """Search calendar entry series with pagination."""

    calendar_entry_series_ro_repo: CalendarEntrySeriesRepositoryReadOnlyProtocol

    async def handle(self, query: SearchCalendarEntrySeriesQuery) -> value_objects.PagedQueryResponse[CalendarEntrySeriesEntity]:
        """Search calendar entry series with pagination."""
        if query.search_query is not None:
            result = await self.calendar_entry_series_ro_repo.paged_search(query.search_query)
            return result

        items = await self.calendar_entry_series_ro_repo.all()
        total = len(items)
        limit = 50
        offset = 0

        return value_objects.PagedQueryResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_next=False,
            has_previous=False,
        )
