"""Query to search push notifications with pagination."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import PushNotificationRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import PushNotificationEntity


@dataclass(frozen=True)
class SearchPushNotificationsQuery(Query):
    """Query to search push notifications."""

    search_query: value_objects.PushNotificationQuery | None = None


class SearchPushNotificationsHandler(
    BaseQueryHandler[
        SearchPushNotificationsQuery,
        value_objects.PagedQueryResponse[PushNotificationEntity],
    ]
):
    """Searches push notifications with pagination."""

    push_notification_ro_repo: PushNotificationRepositoryReadOnlyProtocol

    async def handle(
        self, query: SearchPushNotificationsQuery
    ) -> value_objects.PagedQueryResponse[PushNotificationEntity]:
        """Search push notifications with pagination.

        Args:
            query: The query containing optional search/filter query object

        Returns:
            PagedQueryResponse with push notification entities
        """
        if query.search_query is not None:
            result = await self.push_notification_ro_repo.paged_search(
                query.search_query
            )
            return result

        items = await self.push_notification_ro_repo.all()
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
