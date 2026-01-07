"""Query to search push subscriptions with pagination."""

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import PushSubscriptionRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.infrastructure import data_objects


class SearchPushSubscriptionsHandler(BaseQueryHandler):
    """Searches push subscriptions with pagination."""

    push_subscription_ro_repo: PushSubscriptionRepositoryReadOnlyProtocol

    async def run(
        self,
        search_query: value_objects.PushSubscriptionQuery | None = None,
    ) -> value_objects.PagedQueryResponse[data_objects.PushSubscription]:
        """Search push subscriptions with pagination.

        Args:
            search_query: Optional search/filter query object with pagination info

        Returns:
            PagedQueryResponse with push subscription entities
        """
        if search_query is not None:
            items = await self.push_subscription_ro_repo.search_query(search_query)
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
            items = await self.push_subscription_ro_repo.all()
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

