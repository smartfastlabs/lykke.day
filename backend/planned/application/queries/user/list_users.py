"""Query to list users with optional pagination."""

from uuid import UUID

from planned.application.unit_of_work import ReadOnlyRepositories
from planned.domain import value_objects
from planned.domain.entities import UserEntity


class ListUsersHandler:
    """Lists users with optional pagination."""

    def __init__(self, ro_repos: ReadOnlyRepositories, user_id: UUID) -> None:
        self._ro_repos = ro_repos
        self.user_id = user_id

    async def run(
        self,
        search_query: value_objects.UserQuery | None = None,
    ) -> list[UserEntity] | value_objects.PagedQueryResponse[UserEntity]:
        """List users with optional pagination.

        Args:
            search_query: Optional search/filter query object with pagination info

        Returns:
            List of users or PagedQueryResponse if pagination is requested
        """
        if search_query is not None:
            items = await self._ro_repos.user_ro_repo.search_query(search_query)
            # Check if pagination is requested
            if search_query.limit is not None or search_query.offset is not None:
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
            return items
        else:
            return await self._ro_repos.user_ro_repo.all()

