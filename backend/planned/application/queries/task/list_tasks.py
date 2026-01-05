"""Query to search tasks with pagination."""

from planned.application.queries.base import BaseQueryHandler
from planned.application.repositories import TaskRepositoryReadOnlyProtocol
from planned.domain import value_objects
from planned.domain.entities import TaskEntity


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
            items = await self.task_ro_repo.search_query(search_query)
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

