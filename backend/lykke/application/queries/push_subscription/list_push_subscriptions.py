"""Query to search push subscriptions with pagination."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import PushSubscriptionRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import PushSubscriptionEntity


@dataclass(frozen=True)
class SearchPushSubscriptionsQuery(Query):
    """Query to search push subscriptions."""

    search_query: value_objects.PushSubscriptionQuery | None = None


class SearchPushSubscriptionsHandler(
    BaseQueryHandler[
        SearchPushSubscriptionsQuery,
        value_objects.PagedQueryResponse[PushSubscriptionEntity],
    ]
):
    """Searches push subscriptions with pagination."""

    push_subscription_ro_repo: PushSubscriptionRepositoryReadOnlyProtocol

    async def handle(
        self, query: SearchPushSubscriptionsQuery
    ) -> value_objects.PagedQueryResponse[PushSubscriptionEntity]:
        """Search push subscriptions with pagination.

        Args:
            query: The query containing optional search/filter query object

        Returns:
            PagedQueryResponse with push subscription entities
        """
        if query.search_query is not None:
            result = await self.push_subscription_ro_repo.paged_search(
                query.search_query
            )
            return result
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
