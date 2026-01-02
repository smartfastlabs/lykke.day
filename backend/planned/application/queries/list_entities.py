"""Generic query to list entities with optional filtering and pagination."""

from dataclasses import dataclass
from typing import Generic, TypeVar
from uuid import UUID

from planned.application.queries.base import Query, QueryHandler
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain import value_objects

EntityT = TypeVar("EntityT")


@dataclass(frozen=True)
class ListEntitiesQuery(Query, Generic[EntityT]):
    """Query to list entities with optional filtering and pagination.

    Attributes:
        user_id: The user making the request
        repository_name: Name of the repository on UoW (e.g., "days", "tasks")
        search_query: Optional search/filter query object
        limit: Maximum number of items to return
        offset: Number of items to skip
        paginate: Whether to return paginated response
    """

    user_id: UUID
    repository_name: str
    search_query: value_objects.BaseQuery | None = None
    limit: int = 50
    offset: int = 0
    paginate: bool = True


class ListEntitiesHandler(
    QueryHandler[
        ListEntitiesQuery[EntityT], list[EntityT] | value_objects.PagedQueryResponse[EntityT]
    ]
):
    """Handles ListEntitiesQuery - lists entities with optional pagination."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def handle(
        self, query: ListEntitiesQuery[EntityT]
    ) -> list[EntityT] | value_objects.PagedQueryResponse[EntityT]:
        """Execute the query.

        Args:
            query: The list entities query

        Returns:
            List of entities or PagedQueryResponse
        """
        async with self._uow_factory.create(query.user_id) as uow:
            repo = getattr(uow, query.repository_name)

            # Get items using search query or all()
            if query.search_query is not None and hasattr(repo, "search_query"):
                items: list[EntityT] = await repo.search_query(query.search_query)
            elif hasattr(repo, "all"):
                items = await repo.all()
            else:
                raise ValueError(
                    f"Repository {query.repository_name} does not support list"
                )

            if not query.paginate:
                return items

            # Apply pagination
            total = len(items)
            start = query.offset
            end = start + query.limit
            paginated_items = items[start:end]

            return value_objects.PagedQueryResponse(
                items=paginated_items,
                total=total,
                limit=query.limit,
                offset=query.offset,
                has_next=end < total,
                has_previous=start > 0,
            )
