"""Command to evaluate and send smart notifications."""

import hashlib
from dataclasses import dataclass
from datetime import date as dt_date, datetime
from typing import Literal
from uuid import UUID

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.commands.push_subscription import (
    SendPushNotificationCommand,
    SendPushNotificationHandler,
)
from lykke.application.gateways.llm_protocol import LLMTool
from lykke.application.llm import LLMHandlerMixin, UseCasePromptInput
from lykke.application.notifications import (
    build_notification_payload_for_smart_notification,
)
from lykke.application.queries.get_llm_prompt_context import (
    GetLLMPromptContextHandler,
    GetLLMPromptContextQuery,
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


class SmartNotificationHandler(
    LLMHandlerMixin, BaseCommandHandler[SmartNotificationCommand, None]
):
    """Evaluates day context using LLM and sends notification if warranted."""

    push_subscription_ro_repo: PushSubscriptionRepositoryReadOnlyProtocol
    name = "notification"
    template_usecase = "notification"

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        get_llm_prompt_context_handler: GetLLMPromptContextHandler,
        send_push_notification_handler: SendPushNotificationHandler,
    ) -> None:
        """Initialize SmartNotificationHandler.

        Args:
            ro_repos: Read-only repositories
            uow_factory: Unit of work factory for creating write transactions
            user_id: User ID for scoping
            get_llm_prompt_context_handler: Handler for prompt context
            send_push_notification_handler: Handler for sending push notifications
        """
        super().__init__(ro_repos, uow_factory, user_id)
        self._get_llm_prompt_context_handler = get_llm_prompt_context_handler
        self._send_push_notification_handler = send_push_notification_handler
        self._triggered_by: str | None = None

    async def handle(self, command: SmartNotificationCommand) -> None:
        """Evaluate day context and send notification if warranted.

        Args:
            command: The command containing user_id and trigger info
        """
        # Check if smart notifications are enabled
        if not settings.SMART_NOTIFICATIONS_ENABLED:
            logger.debug("Smart notifications are disabled")
            return

        self._triggered_by = command.triggered_by
        await self.run_llm()

    async def build_prompt_input(self, date: dt_date) -> UseCasePromptInput:
        prompt_context = await self._get_llm_prompt_context_handler.handle(
            GetLLMPromptContextQuery(date=date)
        )
        return UseCasePromptInput(prompt_context=prompt_context)

    def build_tools(
        self,
        *,
        current_time: datetime,
        prompt_context: value_objects.LLMPromptContext,
        llm_provider: value_objects.LLMProvider,
    ) -> list[LLMTool]:
        async def decide_notification(
            should_notify: bool,
            message: str | None = None,
            priority: Literal["high", "medium", "low"] | None = None,
            reason: str | None = None,
        ) -> None:
            """Send a smart notification if warranted."""
            if not should_notify:
                logger.debug(
                    "LLM decided not to send notification for user %s",
                    self.user_id,
                )
                return None
            decision = value_objects.NotificationDecision(
                message=message or "",
                priority=priority or "medium",
                reason=reason,
            )
            if decision.priority != "high":
                logger.debug(
                    "LLM decided to send %s priority notification for user %s",
                    decision.priority,
                    self.user_id,
                )
                return None

            day_context_snapshot = serialize_day_context(prompt_context, current_time)
            message_hash = hashlib.sha256(decision.message.encode("utf-8")).hexdigest()
            payload = build_notification_payload_for_smart_notification(decision)

            try:
                subscriptions = await self.push_subscription_ro_repo.all()
                if not subscriptions:
                    logger.debug(
                        "No push subscriptions found for user %s",
                        self.user_id,
                    )
                    return None

                await self._send_push_notification_handler.handle(
                    SendPushNotificationCommand(
                        subscriptions=subscriptions,
                        content=payload,
                        message=decision.message,
                        priority=decision.priority,
                        reason=decision.reason,
                        day_context_snapshot=day_context_snapshot,
                        message_hash=message_hash,
                        triggered_by=self._triggered_by,
                        llm_provider=llm_provider.value,
                    )
                )
                logger.info(
                    "Sent smart notification to %s subscription(s) for user %s",
                    len(subscriptions),
                    self.user_id,
                )
            except Exception as exc:  # pylint: disable=broad-except
                logger.error(
                    "Failed to send push notification for user %s: %s",
                    self.user_id,
                    exc,
                )
                logger.exception(exc)
            return None

        return [
            LLMTool(
                name="decide_notification",
                callback=decide_notification,
                description="Decide whether to send a smart notification.",
            )
        ]
