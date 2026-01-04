"""Command to create a new push subscription."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.infrastructure import data_objects


class CreatePushSubscriptionHandler:
    """Creates a new push subscription."""

    def __init__(self, uow_factory: UnitOfWorkFactory, user_id: UUID) -> None:
        self._uow_factory = uow_factory
        self.user_id = user_id

    async def run(
        self, subscription: data_objects.PushSubscription
    ) -> data_objects.PushSubscription:
        """Create a new push subscription.

        Args:
            subscription: The push subscription entity to create

        Returns:
            The created push subscription entity
        """
        async with self._uow_factory.create(self.user_id) as uow:
            created_subscription = await uow.push_subscription_rw_repo.put(subscription)
            await uow.commit()
            return created_subscription

