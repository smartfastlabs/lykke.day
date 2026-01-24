"""Command to send a push notification."""

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.gateways.web_push_protocol import WebPushGatewayProtocol
from lykke.application.unit_of_work import ReadOnlyRepositories, UnitOfWorkFactory
from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.entities import PushNotificationEntity, PushSubscriptionEntity


@dataclass(frozen=True)
class SendPushNotificationCommand(Command):
    """Command to send a push notification to one or more subscriptions."""

    subscriptions: list[PushSubscriptionEntity]
    content: str | dict | value_objects.NotificationPayload
    message: str | None = None
    priority: str | None = None
    reason: str | None = None
    day_context_snapshot: dict[str, Any] | None = None
    message_hash: str | None = None
    triggered_by: str | None = None
    llm_provider: str | None = None


class SendPushNotificationHandler(
    BaseCommandHandler[SendPushNotificationCommand, None]
):
    """Sends push notifications to subscriptions and tracks them."""

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        web_push_gateway: WebPushGatewayProtocol,
    ) -> None:
        """Initialize SendPushNotificationHandler.

        Args:
            ro_repos: Read-only repositories
            uow_factory: Unit of work factory
            user_id: User ID for scoping
            web_push_gateway: Web push notification gateway
        """
        super().__init__(ro_repos, uow_factory, user_id)
        self._web_push_gateway = web_push_gateway

    async def handle(self, command: SendPushNotificationCommand) -> None:
        """Send push notifications to all subscriptions and track the results.

        Args:
            command: The command containing the subscriptions and content
        """
        if not command.subscriptions:
            logger.warning("No subscriptions provided to send push notification")
            return

        # Serialize content to JSON string for storage
        content_str: str
        if isinstance(command.content, value_objects.NotificationPayload):
            content_dict = dataclass_to_json_dict(command.content)
            filtered_content = {k: v for k, v in content_dict.items() if v is not None}
            content_str = json.dumps(filtered_content)
        elif isinstance(command.content, dict):
            content_str = json.dumps(command.content)
        else:
            content_str = command.content

        # Track results for each subscription
        successful_subscription_ids: list = []
        failed_subscription_ids: list = []
        error_messages: list[str] = []

        # Send to each subscription
        for subscription in command.subscriptions:
            try:
                logger.info(
                    f"Sending push notification to subscription {subscription.id}"
                )
                await self._web_push_gateway.send_notification(
                    subscription=subscription,
                    content=command.content,
                )
                successful_subscription_ids.append(subscription.id)
                logger.info(
                    f"Successfully sent push notification to subscription {subscription.id}"
                )
            except Exception as e:
                failed_subscription_ids.append(subscription.id)
                error_msg = f"Subscription {subscription.id}: {e!s}"
                error_messages.append(error_msg)
                logger.error(
                    f"Failed to send push notification to subscription {subscription.id}: {e}"
                )

        # Create PushNotificationEntity to track this send attempt
        # Use the user_id from the first subscription (all should be for the same user)
        user_id = command.subscriptions[0].user_id
        all_subscription_ids = successful_subscription_ids + failed_subscription_ids

        if not all_subscription_ids:
            # No subscriptions to track
            return

        # Determine overall status
        if failed_subscription_ids and successful_subscription_ids:
            status = "partial_failure"
            error_message = f"Some notifications failed: {'; '.join(error_messages)}"
        elif failed_subscription_ids:
            status = "failed"
            error_message = f"All notifications failed: {'; '.join(error_messages)}"
        else:
            status = "success"
            error_message = None

        # Create and save the notification entity
        async with self.new_uow(user_id) as uow:
            notification = PushNotificationEntity(
                user_id=user_id,
                push_subscription_ids=all_subscription_ids,
                content=content_str,
                status=status,
                error_message=error_message,
                message=command.message,
                priority=command.priority,
                reason=command.reason,
                day_context_snapshot=command.day_context_snapshot or {},
                message_hash=command.message_hash,
                triggered_by=command.triggered_by,
                llm_provider=command.llm_provider,
            )
            notification.create()
            await uow.create(notification)
            logger.info(
                f"Created PushNotificationEntity {notification.id} for {len(all_subscription_ids)} "
                f"subscription(s): {len(successful_subscription_ids)} successful, "
                f"{len(failed_subscription_ids)} failed"
            )
