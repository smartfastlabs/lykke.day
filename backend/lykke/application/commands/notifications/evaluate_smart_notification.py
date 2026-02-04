"""Command to evaluate and send smart notifications."""

import hashlib
import json
from dataclasses import dataclass
from datetime import date as dt_date, datetime, timedelta
from typing import Literal
from uuid import UUID

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.commands.push_subscription import (
    SendPushNotificationCommand,
    SendPushNotificationHandler,
)
from lykke.application.gateways.llm_gateway_factory_protocol import (
    LLMGatewayFactoryProtocol,
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
from lykke.application.repositories import (
    PushNotificationRepositoryReadOnlyProtocol,
    PushSubscriptionRepositoryReadOnlyProtocol,
)
from lykke.core.config import settings
from lykke.core.utils.llm_snapshot import build_referenced_entities
from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.entities import PushNotificationEntity, UserEntity


@dataclass(frozen=True)
class SmartNotificationCommand(Command):
    """Command to evaluate day context and send smart notification if warranted."""

    user: UserEntity
    triggered_by: str | None = None  # "scheduled", "task_status_change", etc.


class SmartNotificationHandler(
    LLMHandlerMixin, BaseCommandHandler[SmartNotificationCommand, None]
):
    """Evaluates day context using LLM and sends notification if warranted."""

    push_notification_ro_repo: PushNotificationRepositoryReadOnlyProtocol
    push_subscription_ro_repo: PushSubscriptionRepositoryReadOnlyProtocol
    llm_gateway_factory: LLMGatewayFactoryProtocol
    get_llm_prompt_context_handler: GetLLMPromptContextHandler
    send_push_notification_handler: SendPushNotificationHandler
    name = "notification"
    template_usecase = "notification"
    _triggered_by: str | None = None

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
        prompt_context = await self.get_llm_prompt_context_handler.handle(
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
                current_time=snapshot_context.current_time,
                llm_provider=snapshot_context.llm_provider,
                system_prompt=snapshot_context.system_prompt,
                referenced_entities=build_referenced_entities(
                    snapshot_context.prompt_context
                ),
                messages=snapshot_context.messages,
                tools=snapshot_context.tools,
                tool_choice=snapshot_context.tool_choice,
                model_params=snapshot_context.model_params,
            )

        async def decide_notification(
            should_notify: bool,
            message: str | None = None,
            priority: Literal["high", "medium", "low"] | None = None,
            reason: str | None = None,
        ) -> None:
            """Decide whether to send a smart notification."""
            if not should_notify:
                logger.debug(
                    f"LLM decided not to send notification for user {self.user.id}",
                )
                return None
            decision = value_objects.NotificationDecision(
                message=message or "",
                priority=priority or "medium",
                reason=reason,
            )
            logger.debug(
                f"LLM decided to send {decision.priority} priority notification for user {self.user.id}",
            )
            if decision.priority not in ["high", "medium"]:
                return
            cooldown_window = current_time - timedelta(minutes=15)
            recent_notifications = await self.push_notification_ro_repo.search(
                value_objects.PushNotificationQuery(sent_after=cooldown_window)
            )
            recent_delivered = [
                notification
                for notification in recent_notifications
                if notification.status in {"success", "partial_failure"}
            ]
            if recent_delivered:
                logger.debug(
                    f"Skipping smart notification for user {self.user.id} due to cooldown window",
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
                        f"No push subscriptions found for user {self.user.id}",
                    )
                    content_str = json.dumps(filtered_content)
                    async with self._uow_factory.create(self.user) as uow:
                        notification = PushNotificationEntity(
                            user_id=self.user.id,
                            push_subscription_ids=[],
                            content=content_str,
                            status="skipped",
                            error_message="no_subscriptions",
                            message=decision.message,
                            priority=decision.priority,
                            message_hash=message_hash,
                            triggered_by=self._triggered_by,
                            llm_snapshot=llm_snapshot,
                            referenced_entities=(
                                llm_snapshot.referenced_entities if llm_snapshot else []
                            ),
                        )
                        await uow.create(notification)
                        await uow.commit()
                    return None

                await self.send_push_notification_handler.handle(
                    SendPushNotificationCommand(
                        subscriptions=subscriptions,
                        content=payload,
                        message=decision.message,
                        priority=decision.priority,
                        message_hash=message_hash,
                        triggered_by=self._triggered_by,
                        llm_snapshot=llm_snapshot,
                        referenced_entities=(
                            llm_snapshot.referenced_entities if llm_snapshot else None
                        ),
                    )
                )
                logger.info(
                    f"Sent smart notification to {len(subscriptions)} subscription(s) for user {self.user.id}",
                )
            except Exception as exc:  # pylint: disable=broad-except
                logger.error(
                    f"Failed to send push notification for user {self.user.id}: {exc}",
                )
                logger.exception(exc)
            return None

        return [LLMTool(callback=decide_notification)]
