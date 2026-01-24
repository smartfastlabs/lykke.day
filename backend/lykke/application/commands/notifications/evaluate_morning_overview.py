"""Command to evaluate and send morning overview notifications."""

import hashlib
import json
from dataclasses import dataclass
from uuid import UUID

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.commands.push_subscription import (
    SendPushNotificationCommand,
    SendPushNotificationHandler,
)
from lykke.application.llm_usecases import LLMUseCaseRunner, MorningOverviewUseCase
from lykke.application.notifications import (
    build_notification_payload_for_smart_notification,
)
from lykke.application.repositories import (
    PushSubscriptionRepositoryReadOnlyProtocol,
    UserRepositoryReadOnlyProtocol,
)
from lykke.application.unit_of_work import ReadOnlyRepositories, UnitOfWorkFactory
from lykke.core.config import settings
from lykke.core.utils.day_context_serialization import serialize_day_context
from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.entities import PushNotificationEntity


@dataclass(frozen=True)
class MorningOverviewCommand(Command):
    """Command to evaluate day context and send morning overview if warranted."""

    user_id: UUID


class MorningOverviewHandler(BaseCommandHandler[MorningOverviewCommand, None]):
    """Evaluates day context using LLM and sends morning overview if warranted."""

    push_subscription_ro_repo: PushSubscriptionRepositoryReadOnlyProtocol
    user_ro_repo: UserRepositoryReadOnlyProtocol

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        llm_usecase_runner: LLMUseCaseRunner,
        morning_overview_usecase: MorningOverviewUseCase,
        send_push_notification_handler: SendPushNotificationHandler,
    ) -> None:
        """Initialize MorningOverviewHandler.

        Args:
            ro_repos: Read-only repositories
            uow_factory: Unit of work factory for creating write transactions
            user_id: User ID for scoping
            llm_usecase_runner: Runner for executing LLM usecases
            morning_overview_usecase: Usecase for morning overview
            send_push_notification_handler: Handler for sending push notifications
        """
        super().__init__(ro_repos, uow_factory, user_id)
        self._llm_usecase_runner = llm_usecase_runner
        self._morning_overview_usecase = morning_overview_usecase
        self._send_push_notification_handler = send_push_notification_handler

    async def handle(self, command: MorningOverviewCommand) -> None:
        """Evaluate day context and send morning overview if warranted.

        Args:
            command: The command containing user_id
        """
        # Check if smart notifications are enabled
        if not settings.SMART_NOTIFICATIONS_ENABLED:
            logger.debug("Smart notifications are disabled")
            return

        # Load user to get LLM provider preference
        try:
            user = await self.user_ro_repo.get(command.user_id)
        except Exception as e:
            logger.error(f"Failed to load user {command.user_id}: {e}")
            return

        # Check if user has LLM provider configured
        if not user.settings or not user.settings.llm_provider:
            logger.debug(
                f"User {command.user_id} has no LLM provider configured, skipping"
            )
            return

        # Check if user has morning overview time configured
        if not user.settings.morning_overview_time:
            logger.debug(
                f"User {command.user_id} has no morning overview time configured, skipping"
            )
            return

        usecase_result = await self._llm_usecase_runner.run(
            usecase=self._morning_overview_usecase
        )
        if usecase_result is None:
            return
        decision = usecase_result.result

        if not isinstance(decision, value_objects.NotificationDecision):
            if not decision:
                logger.debug(
                    f"LLM decided not to send morning overview for user {command.user_id}"
                )
                return
            logger.error(
                f"Unexpected LLM result for user {command.user_id}: {decision}"
            )
            return

        day_context_snapshot = serialize_day_context(
            usecase_result.prompt_context, usecase_result.current_time
        )
        message_hash = hashlib.sha256(decision.message.encode("utf-8")).hexdigest()
        payload = build_notification_payload_for_smart_notification(decision)
        content_dict = dataclass_to_json_dict(payload)
        filtered_content = {k: v for k, v in content_dict.items() if v is not None}
        content_str = json.dumps(filtered_content)

        # Send push notification
        try:
            # Load all push subscriptions for user
            subscriptions = await self.push_subscription_ro_repo.all()

            if not subscriptions:
                logger.debug(f"No push subscriptions found for user {command.user_id}")
                async with self.new_uow(command.user_id) as uow:
                    notification = PushNotificationEntity(
                        user_id=command.user_id,
                        push_subscription_ids=[],
                        content=content_str,
                        status="skipped",
                        error_message="no_subscriptions",
                        message=decision.message,
                        priority=decision.priority,
                        reason=decision.reason,
                        day_context_snapshot=day_context_snapshot,
                        message_hash=message_hash,
                        triggered_by="morning_overview",
                        llm_provider=usecase_result.llm_provider.value,
                    )
                    notification.create()
                    await uow.create(notification)
                    await uow.commit()
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
                    triggered_by="morning_overview",
                    llm_provider=usecase_result.llm_provider.value,
                )
            )

            logger.info(
                f"Sent morning overview to {len(subscriptions)} subscription(s) for user {command.user_id}"
            )
        except Exception as e:
            # Log but don't fail - notification is already saved
            logger.error(
                f"Failed to send morning overview for user {command.user_id}: {e}"
            )
            logger.exception(e)
