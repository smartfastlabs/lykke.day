"""Query to search calendar entry series with pagination."""

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import CalendarEntrySeriesRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntrySeriesEntity


class SearchCalendarEntrySeriesHandler(BaseQueryHandler):
    """Search calendar entry series with pagination."""

    calendar_entry_series_ro_repo: CalendarEntrySeriesRepositoryReadOnlyProtocol

    async def run(
        self,
        search_query: value_objects.CalendarEntrySeriesQuery | None = None,
    ) -> value_objects.PagedQueryResponse[CalendarEntrySeriesEntity]:
        """Search calendar entry series with pagination."""
        if search_query is not None:
            result = await self.calendar_entry_series_ro_repo.paged_search(search_query)
            return value_objects.PagedQueryResponse(
                **result.__dict__,
            )

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
