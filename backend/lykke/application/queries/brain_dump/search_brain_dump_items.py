"""Query to search brain dump items with pagination."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import BrainDumpRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import BrainDumpEntity


@dataclass(frozen=True)
class SearchBrainDumpItemsQuery(Query):
    """Query to search brain dump items."""

    search_query: value_objects.BrainDumpQuery | None = None


class SearchBrainDumpItemsHandler(
    BaseQueryHandler[
        SearchBrainDumpItemsQuery, value_objects.PagedQueryResponse[BrainDumpEntity]
    ]
):
    """Searches brain dump items with pagination."""

    brain_dump_ro_repo: BrainDumpRepositoryReadOnlyProtocol

    async def handle(
        self, query: SearchBrainDumpItemsQuery
    ) -> value_objects.PagedQueryResponse[BrainDumpEntity]:
        """Search brain dump items with pagination."""
        if query.search_query is not None:
            return await self.brain_dump_ro_repo.paged_search(query.search_query)

        items = await self.brain_dump_ro_repo.all()
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
