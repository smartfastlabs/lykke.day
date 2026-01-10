"""Command to update an existing push subscription."""

from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler
from lykke.domain import data_objects
from lykke.domain.value_objects import PushSubscriptionUpdateObject


class UpdatePushSubscriptionHandler(BaseCommandHandler):
    """Updates an existing push subscription."""

    async def run(
        self,
        subscription_id: UUID,
        update_data: PushSubscriptionUpdateObject,
    ) -> data_objects.PushSubscription:
        """Update an existing push subscription.

        Args:
            subscription_id: The ID of the push subscription to update.
            update_data: The update data containing optional fields.

        Returns:
            The updated push subscription data object.
        """
        async with self.new_uow() as uow:
            # Get the existing push subscription
            subscription = await uow.push_subscription_ro_repo.get(subscription_id)

            # Update fields if provided
            if update_data.device_name is not None:
                subscription = data_objects.PushSubscription(
                    id=subscription.id,
                    user_id=subscription.user_id,
                    device_name=update_data.device_name,
                    endpoint=subscription.endpoint,
                    p256dh=subscription.p256dh,
                    auth=subscription.auth,
                    created_at=subscription.created_at,
                )

            # Add to UoW for saving
            uow.add(subscription)
            return subscription

