"""Generic query to list entities with optional filtering and pagination."""

from typing import TypeVar
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain import value_objects

EntityT = TypeVar("EntityT")


class ListEntitiesHandler:
    """Lists entities with optional filtering and pagination."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def list_entities(
        self,
        user_id: UUID,
        repository_name: str,
        search_query: value_objects.BaseQuery | None = None,
        limit: int = 50,
        offset: int = 0,
        paginate: bool = True,
    ) -> list[EntityT] | value_objects.PagedQueryResponse[EntityT]:
        """List entities with optional filtering and pagination.

        Args:
            user_id: The user making the request
            repository_name: Name of the repository on UoW (e.g., "days", "tasks")
            search_query: Optional search/filter query object
            limit: Maximum number of items to return
            offset: Number of items to skip
            paginate: Whether to return paginated response

        Returns:
            List of entities or PagedQueryResponse
        """
        async with self._uow_factory.create(user_id) as uow:
            repo = getattr(uow, repository_name)

            # Get items using search query or all()
            if search_query is not None and hasattr(repo, "search_query"):
                items: list[EntityT] = await repo.search_query(search_query)
            elif hasattr(repo, "all"):
                items = await repo.all()
            else:
                raise ValueError(
                    f"Repository {repository_name} does not support list"
                )

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
