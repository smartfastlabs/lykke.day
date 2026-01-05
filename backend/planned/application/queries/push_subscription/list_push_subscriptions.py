"""Query to search push subscriptions with pagination."""

from uuid import UUID

from planned.application.unit_of_work import ReadOnlyRepositories
from planned.domain import value_objects
from planned.infrastructure import data_objects


class SearchPushSubscriptionsHandler:
    """Searches push subscriptions with pagination."""

    def __init__(self, ro_repos: ReadOnlyRepositories, user_id: UUID) -> None:
        self._ro_repos = ro_repos
        self.user_id = user_id

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
            items = await self._ro_repos.push_subscription_ro_repo.search_query(search_query)
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
            items = await self._ro_repos.push_subscription_ro_repo.all()
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

