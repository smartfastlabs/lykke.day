"""Query to search task definitions with pagination."""

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import TaskDefinitionRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain import data_objects


class SearchTaskDefinitionsHandler(BaseQueryHandler):
    """Searches task definitions with pagination."""

    task_definition_ro_repo: TaskDefinitionRepositoryReadOnlyProtocol

    async def run(
        self,
        search_query: value_objects.TaskDefinitionQuery | None = None,
    ) -> value_objects.PagedQueryResponse[data_objects.TaskDefinition]:
        """Search task definitions with pagination.

        Args:
            search_query: Optional search/filter query object with pagination info

        Returns:
            PagedQueryResponse with task definitions
        """
        if search_query is not None:
            result = await self.task_definition_ro_repo.paged_search(search_query)
            return result
        else:
            items = await self.task_definition_ro_repo.all()
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

