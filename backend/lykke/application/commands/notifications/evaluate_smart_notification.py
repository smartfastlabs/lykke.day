"""Command to evaluate and send smart notifications."""

import hashlib
import json
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
from lykke.core.utils.llm_snapshot import build_referenced_entities
from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.entities import PushNotificationEntity


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
        def build_llm_snapshot(
            *,
            tool_name: str,
            tool_args: dict[str, object | None],
        ) -> value_objects.LLMRunResultSnapshot | None:
            snapshot_context = self._llm_snapshot_context
            if snapshot_context is None:
                return None
            return value_objects.LLMRunResultSnapshot(
                tool_calls=[
                    value_objects.LLMToolCallResultSnapshot(
                        tool_name=tool_name,
                        arguments=tool_args,
                        result=None,
                    )
                ],
                prompt_context=serialize_day_context(
                    snapshot_context.prompt_context,
                    current_time=snapshot_context.current_time,
                ),
                current_time=snapshot_context.current_time,
                llm_provider=snapshot_context.llm_provider,
                system_prompt=snapshot_context.system_prompt,
                context_prompt=snapshot_context.context_prompt,
                ask_prompt=snapshot_context.ask_prompt,
                tools_prompt=snapshot_context.tools_prompt,
                referenced_entities=build_referenced_entities(
                    snapshot_context.prompt_context
                ),
            )

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

            llm_snapshot = build_llm_snapshot(
                tool_name="decide_notification",
                tool_args={
                    "should_notify": should_notify,
                    "message": message,
                    "priority": priority,
                    "reason": reason,
                },
            )
            message_hash = hashlib.sha256(decision.message.encode("utf-8")).hexdigest()
            payload = build_notification_payload_for_smart_notification(decision)
            content_dict = dataclass_to_json_dict(payload)
            filtered_content = {k: v for k, v in content_dict.items() if v is not None}

            try:
                subscriptions = await self.push_subscription_ro_repo.all()
                if not subscriptions:
                    logger.debug(
                        "No push subscriptions found for user %s",
                        self.user_id,
                    )
                    content_str = json.dumps(filtered_content)
                    async with self._uow_factory.create(self.user_id) as uow:
                        notification = PushNotificationEntity(
                            user_id=self.user_id,
                            push_subscription_ids=[],
                            content=content_str,
                            status="skipped",
                            error_message="no_subscriptions",
                            message=decision.message,
                            priority=decision.priority,
                            message_hash=message_hash,
                            triggered_by=self._triggered_by,
                            llm_snapshot=llm_snapshot,
                        )
                        notification.create()
                        await uow.create(notification)
                        await uow.commit()
                    return None

                await self._send_push_notification_handler.handle(
                    SendPushNotificationCommand(
                        subscriptions=subscriptions,
                        content=payload,
                        message=decision.message,
                        priority=decision.priority,
                        message_hash=message_hash,
                        triggered_by=self._triggered_by,
                        llm_snapshot=llm_snapshot,
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
