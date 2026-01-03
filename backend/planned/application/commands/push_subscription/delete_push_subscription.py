"""Command to delete a push subscription."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory


class DeletePushSubscriptionHandler:
    """Deletes a push subscription."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def run(
        self, user_id: UUID, subscription_id: UUID
    ) -> None:
        """Delete a push subscription.

        Args:
            user_id: The user making the request
            subscription_id: The ID of the push subscription to delete

        Raises:
            NotFoundError: If push subscription not found
        """
        async with self._uow_factory.create(user_id) as uow:
            subscription = await uow.push_subscriptions.get(subscription_id)
            await uow.push_subscriptions.delete(subscription)
            await uow.commit()

