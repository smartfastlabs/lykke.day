"""Query to search calendar entries with pagination."""

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import CalendarEntryRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntryEntity


class SearchCalendarEntriesHandler(BaseQueryHandler):
    """Searches calendar entries with pagination."""

    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol

    async def run(
        self,
        search_query: value_objects.CalendarEntryQuery | None = None,
    ) -> value_objects.PagedQueryResponse[CalendarEntryEntity]:
        """Search calendar entries with pagination.

        Args:
            search_query: Optional search/filter query object with pagination info

        Returns:
            PagedQueryResponse with calendar entries
        """
        if search_query is not None:
            result = await self.calendar_entry_ro_repo.paged_search(search_query)
            return result
        else:
            items = await self.calendar_entry_ro_repo.all()
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
