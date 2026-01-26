"""Query to search triggers with pagination."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import TriggerRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import TriggerEntity


@dataclass(frozen=True)
class SearchTriggersQuery(Query):
    """Query to search triggers."""

    search_query: value_objects.TriggerQuery | None = None


class SearchTriggersHandler(
    BaseQueryHandler[
        SearchTriggersQuery,
        value_objects.PagedQueryResponse[TriggerEntity],
    ]
):
    """Searches triggers with pagination."""

    trigger_ro_repo: TriggerRepositoryReadOnlyProtocol

    async def handle(
        self, query: SearchTriggersQuery
    ) -> value_objects.PagedQueryResponse[TriggerEntity]:
        """Search triggers with pagination."""
        if query.search_query is not None:
            return await self.trigger_ro_repo.paged_search(query.search_query)

        items = await self.trigger_ro_repo.all()
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
