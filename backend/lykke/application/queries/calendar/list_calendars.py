"""Query to search calendars with pagination."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import CalendarRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntity


@dataclass(frozen=True)
class SearchCalendarsQuery(Query):
    """Query to search calendars."""

    search_query: value_objects.CalendarQuery | None = None


class SearchCalendarsHandler(
    BaseQueryHandler[
        SearchCalendarsQuery, value_objects.PagedQueryResponse[CalendarEntity]
    ]
):
    """Searches calendars with pagination."""

    calendar_ro_repo: CalendarRepositoryReadOnlyProtocol

    async def handle(
        self, query: SearchCalendarsQuery
    ) -> value_objects.PagedQueryResponse[CalendarEntity]:
        """Search calendars with pagination.

        Args:
            query: The query containing optional search/filter query object

        Returns:
            PagedQueryResponse with calendars
        """
        if query.search_query is not None:
            result = await self.calendar_ro_repo.paged_search(query.search_query)
            return result
        else:
            items = await self.calendar_ro_repo.all()
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
