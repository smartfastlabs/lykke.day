"""Query to list push subscriptions."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.infrastructure import data_objects


class ListPushSubscriptionsHandler:
    """Lists push subscriptions."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def run(
        self, user_id: UUID
    ) -> list[data_objects.PushSubscription]:
        """List push subscriptions.

        Args:
            user_id: The user making the request

        Returns:
            List of push subscription entities
        """
        async with self._uow_factory.create(user_id) as uow:
            return await uow.push_subscriptions.all()

