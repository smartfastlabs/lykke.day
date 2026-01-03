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
        limit: int = 50,
        offset: int = 0,
        paginate: bool = True,
    ) -> list[CalendarEntity] | value_objects.PagedQueryResponse[CalendarEntity]:
        """List calendars with optional pagination.

        Args:
            user_id: The user making the request
            limit: Maximum number of items to return
            offset: Number of items to skip
            paginate: Whether to return paginated response

        Returns:
            List of calendars or PagedQueryResponse
        """
        items = await self._ro_repos.calendar_ro_repo.all()

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

