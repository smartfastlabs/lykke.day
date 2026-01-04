"""Query to list calendars with optional pagination."""

from uuid import UUID

from planned.application.unit_of_work import ReadOnlyRepositories
from planned.domain import value_objects
from planned.domain.entities import CalendarEntity


class ListCalendarsHandler:
    """Lists calendars with optional pagination."""

    def __init__(self, ro_repos: ReadOnlyRepositories) -> None:
        self._ro_repos = ro_repos

    async def run(
        self,
        user_id: UUID,
        search_query: value_objects.CalendarQuery | None = None,
    ) -> list[CalendarEntity] | value_objects.PagedQueryResponse[CalendarEntity]:
        """List calendars with optional pagination.

        Args:
            user_id: The user making the request
            search_query: Optional search/filter query object with pagination info

        Returns:
            List of calendars or PagedQueryResponse if pagination is requested
        """
        if search_query is not None:
            items = await self._ro_repos.calendar_ro_repo.search_query(search_query)
            # Check if pagination is requested
            if search_query.limit is not None or search_query.offset is not None:
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
            return items
        else:
            return await self._ro_repos.calendar_ro_repo.all()

