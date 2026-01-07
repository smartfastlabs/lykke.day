"""Query to search auth tokens with pagination."""

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import AuthTokenRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.infrastructure import data_objects


class SearchAuthTokensHandler(BaseQueryHandler):
    """Searches auth tokens with pagination."""

    auth_token_ro_repo: AuthTokenRepositoryReadOnlyProtocol

    async def run(
        self,
        search_query: value_objects.AuthTokenQuery | None = None,
    ) -> value_objects.PagedQueryResponse[data_objects.AuthToken]:
        """Search auth tokens with pagination.

        Args:
            search_query: Optional search/filter query object with pagination info

        Returns:
            PagedQueryResponse with auth tokens
        """
        if search_query is not None:
            items = await self.auth_token_ro_repo.search_query(search_query)
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
            items = await self.auth_token_ro_repo.all()
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

