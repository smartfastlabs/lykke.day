"""Query to list push subscriptions."""

from uuid import UUID

from planned.application.unit_of_work import ReadOnlyRepositories
from planned.infrastructure import data_objects


class ListPushSubscriptionsHandler:
    """Lists push subscriptions."""

    def __init__(self, ro_repos: ReadOnlyRepositories) -> None:
        self._ro_repos = ro_repos

    async def run(
        self, user_id: UUID
    ) -> list[data_objects.PushSubscription]:
        """List push subscriptions.

        Args:
            user_id: The user making the request

        Returns:
            List of push subscription entities
        """
        return await self._ro_repos.push_subscription_ro_repo.all()

