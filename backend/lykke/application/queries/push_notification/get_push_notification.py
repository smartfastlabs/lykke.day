"""Query to get a push notification by ID."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import PushNotificationRepositoryReadOnlyProtocol
from lykke.domain.entities import PushNotificationEntity


@dataclass(frozen=True)
class GetPushNotificationQuery(Query):
    """Query to get a push notification by ID."""

    push_notification_id: UUID


class GetPushNotificationHandler(
    BaseQueryHandler[GetPushNotificationQuery, PushNotificationEntity]
):
    """Retrieves a single push notification by ID."""

    push_notification_ro_repo: PushNotificationRepositoryReadOnlyProtocol

    async def handle(self, query: GetPushNotificationQuery) -> PushNotificationEntity:
        """Get a single push notification by ID.

        Args:
            query: The query containing the push notification ID

        Returns:
            The push notification entity

        Raises:
            NotFoundError: If push notification not found
        """
        return await self.push_notification_ro_repo.get(query.push_notification_id)
