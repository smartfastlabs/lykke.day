"""Command to create a new push subscription."""

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler
from lykke.domain.entities import PushSubscriptionEntity


class CreatePushSubscriptionHandler(BaseCommandHandler):
    """Creates a new push subscription."""

    async def run(
        self, subscription: PushSubscriptionEntity
    ) -> PushSubscriptionEntity:
        """Create a new push subscription.

        Args:
            subscription: The push subscription entity to create

        Returns:
            The created push subscription entity
        """
        logger.info(
            f"Creating push subscription: {subscription.id} for user {subscription.user_id}"
        )
        async with self.new_uow() as uow:
            logger.info(f"Calling uow.create() for subscription {subscription.id}")
            await uow.create(subscription)
            logger.info(f"Successfully created push subscription {subscription.id}")
            return subscription
