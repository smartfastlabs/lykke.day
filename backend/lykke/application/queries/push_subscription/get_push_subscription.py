"""Query to get a push subscription by ID."""

from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import PushSubscriptionRepositoryReadOnlyProtocol
from lykke.domain.entities import PushSubscriptionEntity


class GetPushSubscriptionHandler(BaseQueryHandler):
    """Retrieves a single push subscription by ID."""

    push_subscription_ro_repo: PushSubscriptionRepositoryReadOnlyProtocol

    async def run(
        self, subscription_id: UUID
    ) -> PushSubscriptionEntity:
        """Get a single push subscription by ID.

        Args:
            subscription_id: The ID of the push subscription to retrieve

        Returns:
            The push subscription data object

        Raises:
            NotFoundError: If push subscription not found
        """
        return await self.push_subscription_ro_repo.get(subscription_id)

