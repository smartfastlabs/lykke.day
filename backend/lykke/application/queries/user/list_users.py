"""Query to search users with pagination."""

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import UserRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity


class SearchUsersHandler(BaseQueryHandler):
    """Searches users with pagination."""

    user_ro_repo: UserRepositoryReadOnlyProtocol

    async def run(
        self,
        search_query: value_objects.UserQuery | None = None,
    ) -> value_objects.PagedQueryResponse[UserEntity]:
        """Search users with pagination.

        Args:
            search_query: Optional search/filter query object with pagination info

        Returns:
            PagedQueryResponse with users
        """
        if search_query is not None:
            result = await self.user_ro_repo.paged_search(search_query)
            return value_objects.PagedQueryResponse(
                **result.__dict__,
            )
        else:
            items = await self.user_ro_repo.all()
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

