"""Query handlers for time block definition operations."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.domain import value_objects
from lykke.domain.entities import TimeBlockDefinitionEntity


@dataclass(frozen=True)
class GetTimeBlockDefinitionQuery(Query):
    """Query to get a time block definition by ID."""

    time_block_definition_id: UUID


@dataclass(frozen=True)
class SearchTimeBlockDefinitionsQuery(Query):
    """Query to search time block definitions."""

    search_query: value_objects.TimeBlockDefinitionQuery


class GetTimeBlockDefinitionHandler(
    BaseQueryHandler[GetTimeBlockDefinitionQuery, TimeBlockDefinitionEntity]
):
    """Query handler to get a single time block definition by ID."""

    async def handle(
        self, query: GetTimeBlockDefinitionQuery
    ) -> TimeBlockDefinitionEntity:
        """Get a time block definition by ID.

        Args:
            query: The query containing the time block definition ID.

        Returns:
            The time block definition entity.
        """
        return await self.time_block_definition_ro_repo.get(
            query.time_block_definition_id
        )


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
        """Search time block definitions with pagination.

        Args:
            query: The query containing search query with pagination parameters.

        Returns:
            Paged response containing time block definitions.
        """
        return await self.time_block_definition_ro_repo.paged_search(query.search_query)
