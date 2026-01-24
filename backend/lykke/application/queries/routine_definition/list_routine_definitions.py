"""Query to search routine definitions with pagination."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import RoutineDefinitionRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import RoutineDefinitionEntity


@dataclass(frozen=True)
class SearchRoutineDefinitionsQuery(Query):
    """Query to search routine definitions."""

    search_query: value_objects.RoutineDefinitionQuery | None = None


class SearchRoutineDefinitionsHandler(
    BaseQueryHandler[
        SearchRoutineDefinitionsQuery,
        value_objects.PagedQueryResponse[RoutineDefinitionEntity],
    ]
):
    """Searches routine definitions with pagination."""

    routine_definition_ro_repo: RoutineDefinitionRepositoryReadOnlyProtocol

    async def handle(
        self, query: SearchRoutineDefinitionsQuery
    ) -> value_objects.PagedQueryResponse[RoutineDefinitionEntity]:
        """Search routine definitions with pagination.

        Args:
            query: The query containing optional search/filter query object

        Returns:
            PagedQueryResponse with routine definitions
        """
        if query.search_query is not None:
            result = await self.routine_definition_ro_repo.paged_search(
                query.search_query
            )
            return result
        else:
            items = await self.routine_definition_ro_repo.all()
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
