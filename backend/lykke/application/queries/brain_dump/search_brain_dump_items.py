"""Query to search brain dumps with pagination."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import BrainDumpRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import BrainDumpEntity


@dataclass(frozen=True)
class SearchBrainDumpsQuery(Query):
    """Query to search brain dumps."""

    search_query: value_objects.BrainDumpQuery | None = None


class SearchBrainDumpsHandler(
    BaseQueryHandler[
        SearchBrainDumpsQuery, value_objects.PagedQueryResponse[BrainDumpEntity]
    ]
):
    """Searches brain dumps with pagination."""

    brain_dump_ro_repo: BrainDumpRepositoryReadOnlyProtocol

    async def handle(
        self, query: SearchBrainDumpsQuery
    ) -> value_objects.PagedQueryResponse[BrainDumpEntity]:
        """Search brain dumps with pagination."""
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
