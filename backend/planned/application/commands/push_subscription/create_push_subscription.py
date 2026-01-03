"""Command to create a new push subscription."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.infrastructure import data_objects


class CreatePushSubscriptionHandler:
    """Creates a new push subscription."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create_push_subscription(
        self, user_id: UUID, subscription: data_objects.PushSubscription
    ) -> data_objects.PushSubscription:
        """Create a new push subscription.

        Args:
            user_id: The user making the request
            subscription: The push subscription entity to create

        Returns:
            The created push subscription entity
        """
        async with self._uow_factory.create(user_id) as uow:
            created_subscription = await uow.push_subscriptions.put(subscription)
            await uow.commit()
            return created_subscription

