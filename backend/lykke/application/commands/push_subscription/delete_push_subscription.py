"""Command to delete a push subscription."""

from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler


class DeletePushSubscriptionHandler(BaseCommandHandler):
    """Deletes a push subscription."""

    async def run(
        self, subscription_id: UUID
    ) -> None:
        """Delete a push subscription.

        Args:
            subscription_id: The ID of the push subscription to delete

        Raises:
            NotFoundError: If push subscription not found
        """
        async with self.new_uow() as uow:
            subscription = await uow.push_subscription_ro_repo.get(subscription_id)
            await uow.delete(subscription)

