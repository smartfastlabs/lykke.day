"""Query handler to search time block definitions."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.domain import value_objects
from lykke.domain.entities import TimeBlockDefinitionEntity


@dataclass(frozen=True)
class SearchTimeBlockDefinitionsQuery(Query):
    """Query to search time block definitions."""

    search_query: value_objects.TimeBlockDefinitionQuery


class SearchTimeBlockDefinitionsHandler(
    BaseQueryHandler[
        SearchTimeBlockDefinitionsQuery,
        value_objects.PagedQueryResponse[TimeBlockDefinitionEntity],
    ]
):
    """Query handler to search time block definitions with pagination."""

    async def handle(
        self, query: SearchTimeBlockDefinitionsQuery
    ) -> value_objects.PagedQueryResponse[TimeBlockDefinitionEntity]:
        """Search time block definitions with pagination."""
        return await self.time_block_definition_ro_repo.paged_search(query.search_query)
