"""Query to search push subscriptions with pagination."""

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import PushSubscriptionRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain import data_objects


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
            result = await self.push_subscription_ro_repo.paged_search(search_query)
            return value_objects.PagedQueryResponse(**result.__dict__)
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

