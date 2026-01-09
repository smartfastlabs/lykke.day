"""Query to search calendars with pagination."""

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import CalendarRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntity


class SearchCalendarsHandler(BaseQueryHandler):
    """Searches calendars with pagination."""

    calendar_ro_repo: CalendarRepositoryReadOnlyProtocol

    async def run(
        self,
        search_query: value_objects.CalendarQuery | None = None,
    ) -> value_objects.PagedQueryResponse[CalendarEntity]:
        """Search calendars with pagination.

        Args:
            search_query: Optional search/filter query object with pagination info

        Returns:
            PagedQueryResponse with calendars
        """
        if search_query is not None:
            result = await self.calendar_ro_repo.paged_search(search_query)
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
