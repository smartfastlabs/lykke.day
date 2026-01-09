"""Query to search calendar entry series with pagination."""

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import (
    CalendarEntrySeriesRepositoryReadOnlyProtocol,
)
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
            items = await self.calendar_entry_series_ro_repo.search_query(
                search_query
            )
            limit = search_query.limit or 50
            offset = search_query.offset or 0
            total = len(items)
            start = offset
            end = start + limit
            paginated_items = items[start:end]

            return value_objects.PagedQueryResponse(
                items=paginated_items,
                total=total,
                limit=limit,
                offset=offset,
                has_next=end < total,
                has_previous=start > 0,
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


