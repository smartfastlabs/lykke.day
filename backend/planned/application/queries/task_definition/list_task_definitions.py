"""Query to search task definitions with pagination."""

from planned.application.queries.base import BaseQueryHandler
from planned.application.repositories import TaskDefinitionRepositoryReadOnlyProtocol
from planned.domain import value_objects
from planned.infrastructure import data_objects


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
            items = await self.task_definition_ro_repo.search_query(search_query)
            limit = search_query.limit or 50
            offset = search_query.offset or 0
            total = len(items)
            start = offset
            end = start + limit
            paginated_items = items[start:end]

            return value_objects.PagedQueryResponse(
                items=paginated_items,
                total=total,
                limit=limit,
                offset=offset,
                has_next=end < total,
                has_previous=start > 0,
            )
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

