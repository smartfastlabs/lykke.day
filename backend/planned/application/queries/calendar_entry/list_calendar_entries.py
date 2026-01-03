"""Query to list calendar entries with optional pagination."""

from uuid import UUID

from planned.application.unit_of_work import ReadOnlyRepositories
from planned.domain import value_objects
from planned.domain.entities import CalendarEntryEntity


class ListCalendarEntriesHandler:
    """Lists calendar entries with optional pagination."""

    def __init__(self, ro_repos: ReadOnlyRepositories) -> None:
        self._ro_repos = ro_repos

    async def run(
        self,
        user_id: UUID,
        search_query: value_objects.BaseQuery | None = None,
        limit: int = 50,
        offset: int = 0,
        paginate: bool = True,
    ) -> list[CalendarEntryEntity] | value_objects.PagedQueryResponse[CalendarEntryEntity]:
        """List calendar entries with optional pagination.

        Args:
            user_id: The user making the request
            search_query: Optional search/filter query object
            limit: Maximum number of items to return
            offset: Number of items to skip
            paginate: Whether to return paginated response

        Returns:
            List of calendar entries or PagedQueryResponse
        """
        if search_query is not None:
            items = await self._ro_repos.calendar_entry_ro_repo.search_query(search_query)
        else:
            items = await self._ro_repos.calendar_entry_ro_repo.all()

        if not paginate:
            return items

        # Apply pagination
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

