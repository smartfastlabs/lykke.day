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
            items = await self.calendar_ro_repo.search_query(search_query)
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
