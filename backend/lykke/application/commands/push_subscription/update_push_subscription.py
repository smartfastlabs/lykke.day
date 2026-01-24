"""Command to update an existing push subscription."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import PushSubscriptionEntity
from lykke.domain.value_objects import PushSubscriptionUpdateObject


@dataclass(frozen=True)
class UpdatePushSubscriptionCommand(Command):
    """Command to update an existing push subscription."""

    subscription_id: UUID
    update_data: PushSubscriptionUpdateObject


class UpdatePushSubscriptionHandler(
    BaseCommandHandler[UpdatePushSubscriptionCommand, PushSubscriptionEntity]
):
    """Updates an existing push subscription."""

    async def handle(
        self, command: UpdatePushSubscriptionCommand
    ) -> PushSubscriptionEntity:
        """Update an existing push subscription.

        Args:
            command: The command containing the push subscription ID and update data.

        Returns:
            The updated push subscription entity.
        """
        async with self.new_uow() as uow:
            # Get the existing push subscription
            subscription = await uow.push_subscription_ro_repo.get(
                command.subscription_id
            )

            # Update fields if provided
            if command.update_data.device_name is not None:
                subscription = PushSubscriptionEntity(
                    id=subscription.id,
                    user_id=subscription.user_id,
                    device_name=command.update_data.device_name,
                    endpoint=subscription.endpoint,
                    p256dh=subscription.p256dh,
                    auth=subscription.auth,
                    created_at=subscription.created_at,
                )

            # Add to UoW for saving
            return uow.add(subscription)
