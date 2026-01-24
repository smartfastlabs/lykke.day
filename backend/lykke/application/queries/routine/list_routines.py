"""Query to search routines with pagination."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import RoutineRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import RoutineEntity


@dataclass(frozen=True)
class SearchRoutinesQuery(Query):
    """Query to search routines."""

    search_query: value_objects.RoutineQuery | None = None


class SearchRoutinesHandler(
    BaseQueryHandler[
        SearchRoutinesQuery, value_objects.PagedQueryResponse[RoutineEntity]
    ]
):
    """Searches routines with pagination."""

    routine_ro_repo: RoutineRepositoryReadOnlyProtocol

    async def handle(
        self, query: SearchRoutinesQuery
    ) -> value_objects.PagedQueryResponse[RoutineEntity]:
        """Search routines with pagination.

        Args:
            query: The query containing optional search/filter query object

        Returns:
            PagedQueryResponse with routines
        """
        if query.search_query is not None:
            result = await self.routine_ro_repo.paged_search(query.search_query)
            return result
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
