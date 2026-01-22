"""Command to evaluate and send smart notifications."""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

from loguru import logger
from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.commands.push_subscription import (
    SendPushNotificationCommand,
    SendPushNotificationHandler,
)
from lykke.application.gateways.llm_gateway_factory import LLMGatewayFactory
from lykke.application.gateways.web_push_protocol import WebPushGatewayProtocol
from lykke.application.llm_usecases import NotificationUseCase
from lykke.application.notifications import (
    build_notification_payload_for_smart_notification,
)
from lykke.application.queries import GetLLMPromptContextHandler
from lykke.application.repositories import (
    PushSubscriptionRepositoryReadOnlyProtocol,
    TemplateRepositoryReadOnlyProtocol,
    UserRepositoryReadOnlyProtocol,
)
from lykke.application.unit_of_work import ReadOnlyRepositories, UnitOfWorkFactory
from lykke.core.config import settings
from lykke.core.exceptions import DomainError
from lykke.core.utils.dates import get_current_date, get_current_datetime_in_timezone
from lykke.core.utils.day_context_serialization import serialize_day_context
from lykke.core.utils.llm_prompt_generation import generate_usecase_prompts
from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.entities import PushNotificationEntity
from lykke.infrastructure.gateways import WebPushGateway


@dataclass(frozen=True)
class SmartNotificationCommand(Command):
    """Command to evaluate day context and send smart notification if warranted."""

    user_id: UUID
    triggered_by: str | None = None  # "scheduled", "task_status_change", etc.


class SmartNotificationHandler(BaseCommandHandler[SmartNotificationCommand, None]):
    """Evaluates day context using LLM and sends notification if warranted."""

    push_subscription_ro_repo: PushSubscriptionRepositoryReadOnlyProtocol
    template_ro_repo: TemplateRepositoryReadOnlyProtocol
    user_ro_repo: UserRepositoryReadOnlyProtocol

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        get_llm_prompt_context_handler: GetLLMPromptContextHandler,
    ) -> None:
        """Initialize SmartNotificationHandler.

        Args:
            ro_repos: Read-only repositories
            uow_factory: Unit of work factory for creating write transactions
            user_id: User ID for scoping
            get_llm_prompt_context_handler: Handler for loading LLM prompt context
        """
        super().__init__(ro_repos, uow_factory, user_id)
        self._get_llm_prompt_context_handler = get_llm_prompt_context_handler

    async def handle(self, command: SmartNotificationCommand) -> None:
        """Evaluate day context and send notification if warranted.

        Args:
            command: The command containing user_id and trigger info
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

        llm_provider = user.settings.llm_provider

        try:
            today = get_current_date(user.settings.timezone)
            usecase = NotificationUseCase(
                get_llm_prompt_context_handler=self._get_llm_prompt_context_handler
            )
            prompt_context = await usecase.build_prompt_context(today)
        except Exception as e:
            logger.error(
                f"Failed to load LLM prompt context for user {command.user_id}: {e}"
            )
            return

        # Serialize day context for storage
        current_time = get_current_datetime_in_timezone(user.settings.timezone)

        # Generate prompts for LLM
        system_prompt, context_prompt, ask_prompt = await generate_usecase_prompts(
            usecase,
            prompt_context,
            current_time,
            template_repo=self.template_ro_repo,
            user_id=command.user_id,
            usecase_config_repo=self.usecase_config_ro_repo,
        )

        # Get LLM gateway
        try:
            llm_gateway = LLMGatewayFactory.create_gateway(llm_provider)
        except DomainError as e:
            logger.error(
                f"Failed to create LLM gateway for provider {llm_provider}: {e}"
            )
            return

        # Call LLM to evaluate
        def on_complete(
            should_notify: bool,
            message: str | None = None,
            priority: Literal["high", "medium", "low"] | None = None,
            reason: str | None = None,
        ) -> value_objects.NotificationDecision | None:
            if not should_notify:
                return None
            return value_objects.NotificationDecision(
                message=message or "",
                priority=priority or "medium",
                reason=reason,
            )

        try:
            decision = await llm_gateway.run_usecase(
                system_prompt,
                context_prompt,
                ask_prompt,
                on_complete=on_complete,
            )
        except Exception as e:
            logger.error(f"LLM evaluation failed for user {command.user_id}: {e}")
            logger.exception(e)
            return

        if not decision:
            logger.debug(
                f"LLM decided not to send notification for user {command.user_id}"
            )
            return

        day_context_snapshot = serialize_day_context(prompt_context, current_time)
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
                        triggered_by=command.triggered_by,
                        llm_provider=llm_provider.value,
                    )
                    notification.create()
                    await uow.create(notification)
                    await uow.commit()
                return

            # Send to all subscriptions
            web_push_gateway: WebPushGatewayProtocol = WebPushGateway()
            send_handler = SendPushNotificationHandler(
                ro_repos=self._ro_repos,
                uow_factory=self._uow_factory,
                user_id=command.user_id,
                web_push_gateway=web_push_gateway,
            )

            await send_handler.handle(
                SendPushNotificationCommand(
                    subscriptions=subscriptions,
                    content=payload,
                    message=decision.message,
                    priority=decision.priority,
                    reason=decision.reason,
                    day_context_snapshot=day_context_snapshot,
                    message_hash=message_hash,
                    triggered_by=command.triggered_by,
                    llm_provider=llm_provider.value,
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
