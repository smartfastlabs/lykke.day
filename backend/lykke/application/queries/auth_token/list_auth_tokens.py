"""Query to search auth tokens with pagination."""

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import AuthTokenRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain import data_objects


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
            result = await self.auth_token_ro_repo.paged_search(search_query)
            return result
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

