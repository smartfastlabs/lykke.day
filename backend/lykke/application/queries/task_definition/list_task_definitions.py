"""Query to search task definitions with pagination."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import TaskDefinitionRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import TaskDefinitionEntity


@dataclass(frozen=True)
class SearchTaskDefinitionsQuery(Query):
    """Query to search task definitions."""

    search_query: value_objects.TaskDefinitionQuery | None = None


class SearchTaskDefinitionsHandler(
    BaseQueryHandler[
        SearchTaskDefinitionsQuery,
        value_objects.PagedQueryResponse[TaskDefinitionEntity],
    ]
):
    """Searches task definitions with pagination."""

    task_definition_ro_repo: TaskDefinitionRepositoryReadOnlyProtocol

    async def handle(
        self, query: SearchTaskDefinitionsQuery
    ) -> value_objects.PagedQueryResponse[TaskDefinitionEntity]:
        """Search task definitions with pagination.

        Args:
            query: The query containing optional search/filter query object

        Returns:
            PagedQueryResponse with task definitions
        """
        if query.search_query is not None:
            result = await self.task_definition_ro_repo.paged_search(query.search_query)
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
