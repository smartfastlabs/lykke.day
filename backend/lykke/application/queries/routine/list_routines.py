"""Query to search routines with pagination."""

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import RoutineRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import RoutineEntity


class SearchRoutinesHandler(BaseQueryHandler):
    """Searches routines with pagination."""

    routine_ro_repo: RoutineRepositoryReadOnlyProtocol

    async def run(
        self,
        search_query: value_objects.RoutineQuery | None = None,
    ) -> value_objects.PagedQueryResponse[RoutineEntity]:
        """Search routines with pagination.

        Args:
            search_query: Optional search/filter query object with pagination info

        Returns:
            PagedQueryResponse with routines
        """
        if search_query is not None:
            result = await self.routine_ro_repo.paged_search(search_query)
            return value_objects.PagedQueryResponse(
                **result.__dict__,
            )
        else:
            items = await self.routine_ro_repo.all()
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

