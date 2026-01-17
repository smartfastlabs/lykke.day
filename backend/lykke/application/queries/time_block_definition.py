"""Query handlers for time block definition operations."""

from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler
from lykke.domain import value_objects
from lykke.domain.entities import TimeBlockDefinitionEntity


class GetTimeBlockDefinitionHandler(BaseQueryHandler):
    """Query handler to get a single time block definition by ID."""

    async def run(self, time_block_definition_id: UUID) -> TimeBlockDefinitionEntity:
        """Get a time block definition by ID.

        Args:
            time_block_definition_id: The ID of the time block definition to retrieve.

        Returns:
            The time block definition entity.
        """
        return await self.time_block_definition_ro_repo.get(time_block_definition_id)


class SearchTimeBlockDefinitionsHandler(BaseQueryHandler):
    """Query handler to search time block definitions with pagination."""

    async def run(
        self,
        search_query: value_objects.TimeBlockDefinitionQuery,
    ) -> value_objects.PagedQueryResponse[TimeBlockDefinitionEntity]:
        """Search time block definitions with pagination.

        Args:
            search_query: The search query with pagination parameters.

        Returns:
            Paged response containing time block definitions.
        """
        return await self.time_block_definition_ro_repo.paged_search(search_query)

