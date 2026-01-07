"""Query to search days with pagination."""

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import DayRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity


class SearchDaysHandler(BaseQueryHandler):
    """Searches days with pagination."""

    day_ro_repo: DayRepositoryReadOnlyProtocol

    async def run(
        self,
        search_query: value_objects.DayQuery | None = None,
    ) -> value_objects.PagedQueryResponse[DayEntity]:
        """Search days with pagination.

        Args:
            search_query: Optional search/filter query object with pagination info

        Returns:
            PagedQueryResponse with days
        """
        if search_query is not None:
            items = await self.day_ro_repo.search_query(search_query)
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
            items = await self.day_ro_repo.all()
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

