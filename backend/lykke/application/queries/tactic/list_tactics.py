"""Query to search tactics with pagination."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import TacticRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import TacticEntity


@dataclass(frozen=True)
class SearchTacticsQuery(Query):
    """Query to search tactics."""

    search_query: value_objects.TacticQuery | None = None


class SearchTacticsHandler(
    BaseQueryHandler[
        SearchTacticsQuery,
        value_objects.PagedQueryResponse[TacticEntity],
    ]
):
    """Searches tactics with pagination."""

    tactic_ro_repo: TacticRepositoryReadOnlyProtocol

    async def handle(
        self, query: SearchTacticsQuery
    ) -> value_objects.PagedQueryResponse[TacticEntity]:
        """Search tactics with pagination."""
        if query.search_query is not None:
            return await self.tactic_ro_repo.paged_search(query.search_query)

        items = await self.tactic_ro_repo.all()
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
