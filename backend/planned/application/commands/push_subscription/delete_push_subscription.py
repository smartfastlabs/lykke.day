"""Command to delete a push subscription."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory


class DeletePushSubscriptionHandler:
    """Deletes a push subscription."""

    def __init__(self, uow_factory: UnitOfWorkFactory, user_id: UUID) -> None:
        self._uow_factory = uow_factory
        self.user_id = user_id

    async def run(
        self, subscription_id: UUID
    ) -> None:
        """Delete a push subscription.

        Args:
            subscription_id: The ID of the push subscription to delete

        Raises:
            NotFoundError: If push subscription not found
        """
        async with self._uow_factory.create(self.user_id) as uow:
            subscription = await uow.push_subscription_rw_repo.get(subscription_id)
            await uow.push_subscription_rw_repo.delete(subscription)
            await uow.commit()

