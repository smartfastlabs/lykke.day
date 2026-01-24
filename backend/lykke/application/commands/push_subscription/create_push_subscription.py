"""Command to create a new push subscription."""

from dataclasses import dataclass

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import PushSubscriptionEntity


@dataclass(frozen=True)
class CreatePushSubscriptionCommand(Command):
    """Command to create a new push subscription."""

    subscription: PushSubscriptionEntity


class CreatePushSubscriptionHandler(
    BaseCommandHandler[CreatePushSubscriptionCommand, PushSubscriptionEntity]
):
    """Creates a new push subscription."""

    async def handle(
        self, command: CreatePushSubscriptionCommand
    ) -> PushSubscriptionEntity:
        """Create a new push subscription.

        Args:
            command: The command containing the push subscription entity to create

        Returns:
            The created push subscription entity
        """
        subscription = command.subscription
        logger.info(
            f"Creating push subscription: {subscription.id} for user {subscription.user_id}"
        )
        async with self.new_uow() as uow:
            logger.info(f"Calling uow.create() for subscription {subscription.id}")
            subscription = await uow.create(subscription)
            logger.info(f"Successfully created push subscription {subscription.id}")
            return subscription
