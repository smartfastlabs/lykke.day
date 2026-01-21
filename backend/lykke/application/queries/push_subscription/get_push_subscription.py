"""Query to get a push subscription by ID."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import PushSubscriptionRepositoryReadOnlyProtocol
from lykke.domain.entities import PushSubscriptionEntity


@dataclass(frozen=True)
class GetPushSubscriptionQuery(Query):
    """Query to get a push subscription by ID."""

    push_subscription_id: UUID


class GetPushSubscriptionHandler(BaseQueryHandler[GetPushSubscriptionQuery, PushSubscriptionEntity]):
    """Retrieves a single push subscription by ID."""

    push_subscription_ro_repo: PushSubscriptionRepositoryReadOnlyProtocol

    async def handle(self, query: GetPushSubscriptionQuery) -> PushSubscriptionEntity:
        """Get a single push subscription by ID.

        Args:
            query: The query containing the push subscription ID

        Returns:
            The push subscription entity

        Raises:
            NotFoundError: If push subscription not found
        """
        return await self.push_subscription_ro_repo.get(query.push_subscription_id)

