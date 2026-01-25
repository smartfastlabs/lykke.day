"""Query to search factoids with pagination."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import FactoidRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import FactoidEntity


@dataclass(frozen=True)
class SearchFactoidsQuery(Query):
    """Query to search factoids."""

    search_query: value_objects.FactoidQuery | None = None


class SearchFactoidsHandler(
    BaseQueryHandler[
        SearchFactoidsQuery,
        value_objects.PagedQueryResponse[FactoidEntity],
    ]
):
    """Searches factoids with pagination."""

    factoid_ro_repo: FactoidRepositoryReadOnlyProtocol

    async def handle(
        self, query: SearchFactoidsQuery
    ) -> value_objects.PagedQueryResponse[FactoidEntity]:
        """Search factoids with pagination.

        Args:
            query: The query containing optional search/filter query object

        Returns:
            PagedQueryResponse with factoids
        """
        if query.search_query is not None:
            return await self.factoid_ro_repo.paged_search(query.search_query)

        items = await self.factoid_ro_repo.all()
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
