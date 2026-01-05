"""Command to create a new push subscription."""

from planned.application.commands.base import BaseCommandHandler
from planned.infrastructure import data_objects


class CreatePushSubscriptionHandler(BaseCommandHandler):
    """Creates a new push subscription."""

    async def run(
        self, subscription: data_objects.PushSubscription
    ) -> data_objects.PushSubscription:
        """Create a new push subscription.

        Args:
            subscription: The push subscription entity to create

        Returns:
            The created push subscription entity
        """
        async with self.new_uow() as uow:
            await uow.create(subscription)
            return subscription

