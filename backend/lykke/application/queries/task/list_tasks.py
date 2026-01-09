"""Query to search tasks with pagination."""

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import TaskRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import TaskEntity


class SearchTasksHandler(BaseQueryHandler):
    """Searches tasks with pagination."""

    task_ro_repo: TaskRepositoryReadOnlyProtocol

    async def run(
        self,
        search_query: value_objects.TaskQuery | None = None,
    ) -> value_objects.PagedQueryResponse[TaskEntity]:
        """Search tasks with pagination.

        Args:
            search_query: Optional search/filter query object with pagination info

        Returns:
            PagedQueryResponse with tasks
        """
        if search_query is not None:
            result = await self.task_ro_repo.paged_search(search_query)
            return result
        else:
            items = await self.task_ro_repo.all()
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

