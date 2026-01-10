"""Query handlers for time block definition operations."""

from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler
from lykke.domain import value_objects
from lykke.domain.data_objects import TimeBlockDefinition


class GetTimeBlockDefinitionHandler(BaseQueryHandler):
    """Query handler to get a single time block definition by ID."""

    async def run(self, time_block_definition_id: UUID) -> TimeBlockDefinition:
        """Get a time block definition by ID.

        Args:
            time_block_definition_id: The ID of the time block definition to retrieve.

        Returns:
            The time block definition entity.
        """
        async with self.new_ro_repo_factory() as repo_factory:
            time_block_definition_repo = (
                repo_factory.time_block_definition_ro_repository()
            )
            return await time_block_definition_repo.get(time_block_definition_id)


class SearchTimeBlockDefinitionsHandler(BaseQueryHandler):
    """Query handler to search time block definitions with pagination."""

    async def run(
        self,
        search_query: value_objects.TimeBlockDefinitionQuery,
    ) -> value_objects.PagedQueryResponse[TimeBlockDefinition]:
        """Search time block definitions with pagination.

        Args:
            search_query: The search query with pagination parameters.

        Returns:
            Paged response containing time block definitions.
        """
        async with self.new_ro_repo_factory() as repo_factory:
            time_block_definition_repo = (
                repo_factory.time_block_definition_ro_repository()
            )
            return await time_block_definition_repo.search(search_query)

