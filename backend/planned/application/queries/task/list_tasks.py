"""Query to list tasks with optional pagination."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain import value_objects
from planned.domain.entities import TaskEntity


class ListTasksHandler:
    """Lists tasks with optional pagination."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def list_tasks(
        self,
        user_id: UUID,
        search_query: value_objects.BaseQuery | None = None,
        limit: int = 50,
        offset: int = 0,
        paginate: bool = False,
    ) -> list[TaskEntity] | value_objects.PagedQueryResponse[TaskEntity]:
        """List tasks with optional pagination.

        Args:
            user_id: The user making the request
            search_query: Optional search/filter query object
            limit: Maximum number of items to return
            offset: Number of items to skip
            paginate: Whether to return paginated response

        Returns:
            List of tasks or PagedQueryResponse
        """
        async with self._uow_factory.create(user_id) as uow:
            if search_query is not None:
                items = await uow.tasks.search_query(search_query)
            else:
                items = await uow.tasks.all()

            if not paginate:
                return items

            # Apply pagination
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

