"""Command to evaluate and send smart notifications."""

import hashlib
from dataclasses import dataclass
from uuid import UUID

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.commands.push_subscription import (
    SendPushNotificationCommand,
    SendPushNotificationHandler,
)
from lykke.application.llm_usecases import LLMUseCaseRunner, NotificationUseCase
from lykke.application.notifications import (
    build_notification_payload_for_smart_notification,
)
from lykke.application.repositories import PushSubscriptionRepositoryReadOnlyProtocol
from lykke.application.unit_of_work import ReadOnlyRepositories, UnitOfWorkFactory
from lykke.core.config import settings
from lykke.core.utils.day_context_serialization import serialize_day_context
from lykke.domain import value_objects


@dataclass(frozen=True)
class SmartNotificationCommand(Command):
    """Command to evaluate day context and send smart notification if warranted."""

    user_id: UUID
    triggered_by: str | None = None  # "scheduled", "task_status_change", etc.


class SmartNotificationHandler(BaseCommandHandler[SmartNotificationCommand, None]):
    """Evaluates day context using LLM and sends notification if warranted."""

    push_subscription_ro_repo: PushSubscriptionRepositoryReadOnlyProtocol

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        llm_usecase_runner: LLMUseCaseRunner,
        notification_usecase: NotificationUseCase,
        send_push_notification_handler: SendPushNotificationHandler,
    ) -> None:
        """Initialize SmartNotificationHandler.

        Args:
            ro_repos: Read-only repositories
            uow_factory: Unit of work factory for creating write transactions
            user_id: User ID for scoping
            llm_usecase_runner: Runner for executing LLM usecases
            notification_usecase: Usecase for smart notifications
            send_push_notification_handler: Handler for sending push notifications
        """
        super().__init__(ro_repos, uow_factory, user_id)
        self._llm_usecase_runner = llm_usecase_runner
        self._notification_usecase = notification_usecase
        self._send_push_notification_handler = send_push_notification_handler

    async def handle(self, command: SmartNotificationCommand) -> None:
        """Evaluate day context and send notification if warranted.

        Args:
            command: The command containing user_id and trigger info
        """
        # Check if smart notifications are enabled
        if not settings.SMART_NOTIFICATIONS_ENABLED:
            logger.debug("Smart notifications are disabled")
            return

        usecase_result = await self._llm_usecase_runner.run(
            usecase=self._notification_usecase
        )
        if usecase_result is None:
            return
        decision = usecase_result.result

        if not isinstance(decision, value_objects.NotificationDecision):
            if not decision:
                logger.debug(
                    f"LLM decided not to send notification for user {command.user_id}"
                )
                return
            logger.error(
                f"Unexpected LLM result for user {command.user_id}: {decision}"
            )
            return
        if decision.priority == "low":
            logger.debug(
                f"LLM decided to send low priority notification for user {command.user_id}"
            )
            return
        if decision.priority == "medium":
            logger.debug(
                f"LLM decided to send medium priority notification for user {command.user_id}"
            )
            return

        day_context_snapshot = serialize_day_context(
            usecase_result.prompt_context, usecase_result.current_time
        )
        message_hash = hashlib.sha256(decision.message.encode("utf-8")).hexdigest()
        payload = build_notification_payload_for_smart_notification(decision)

        # Send push notification
        try:
            # Load all push subscriptions for user
            subscriptions = await self.push_subscription_ro_repo.all()

            if not subscriptions:
                logger.debug(f"No push subscriptions found for user {command.user_id}")
                return

            # Send to all subscriptions
            await self._send_push_notification_handler.handle(
                SendPushNotificationCommand(
                    subscriptions=subscriptions,
                    content=payload,
                    message=decision.message,
                    priority=decision.priority,
                    reason=decision.reason,
                    day_context_snapshot=day_context_snapshot,
                    message_hash=message_hash,
                    triggered_by=command.triggered_by,
                    llm_provider=usecase_result.llm_provider.value,
                )
            )

            logger.info(
                f"Sent smart notification to {len(subscriptions)} subscription(s) for user {command.user_id}"
            )
        except Exception as e:
            # Log but don't fail - notification is already saved
            logger.error(
                f"Failed to send push notification for user {command.user_id}: {e}"
            )
            logger.exception(e)
