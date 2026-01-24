"""Command to delete a push subscription."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command


@dataclass(frozen=True)
class DeletePushSubscriptionCommand(Command):
    """Command to delete a push subscription."""

    subscription_id: UUID


class DeletePushSubscriptionHandler(
    BaseCommandHandler[DeletePushSubscriptionCommand, None]
):
    """Deletes a push subscription."""

    async def handle(self, command: DeletePushSubscriptionCommand) -> None:
        """Delete a push subscription.

        Args:
            command: The command containing the push subscription ID to delete

        Raises:
            NotFoundError: If push subscription not found
        """
        async with self.new_uow() as uow:
            subscription = await uow.push_subscription_ro_repo.get(
                command.subscription_id
            )
            await uow.delete(subscription)
