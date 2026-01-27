"""Command to evaluate and send kiosk notifications."""

import hashlib
from dataclasses import dataclass
from datetime import UTC, date as dt_date, datetime
from typing import Literal
from uuid import UUID

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.gateways.llm_protocol import LLMTool
from lykke.application.gateways.pubsub_protocol import PubSubGatewayProtocol
from lykke.application.llm import LLMHandlerMixin, UseCasePromptInput
from lykke.application.queries.get_llm_prompt_context import (
    GetLLMPromptContextHandler,
    GetLLMPromptContextQuery,
)
from lykke.application.unit_of_work import ReadOnlyRepositories, UnitOfWorkFactory
from lykke.core.config import settings
from lykke.core.utils.day_context_serialization import serialize_day_context
from lykke.core.utils.llm_snapshot import build_referenced_entities
from lykke.domain import value_objects


@dataclass(frozen=True)
class KioskNotificationCommand(Command):
    """Command to evaluate day context and send kiosk notification if warranted."""

    user_id: UUID
    triggered_by: str | None = None  # "scheduled", etc.


@dataclass(frozen=True)
class KioskNotificationDecision:
    """Decision from LLM about whether to send a kiosk notification."""

    message: str  # The notification text to read out
    category: str  # "calendar_event", "routine", "task_reminder", "time_block_change", etc.
    reason: str | None = None  # Why the LLM decided to notify (for debugging)


class KioskNotificationHandler(
    LLMHandlerMixin, BaseCommandHandler[KioskNotificationCommand, None]
):
    """Evaluates day context using LLM and sends kiosk notification if warranted."""

    pubsub_gateway: PubSubGatewayProtocol
    name = "kiosk_notification"
    template_usecase = "kiosk_notification"

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        get_llm_prompt_context_handler: GetLLMPromptContextHandler,
        pubsub_gateway: PubSubGatewayProtocol,
    ) -> None:
        """Initialize KioskNotificationHandler.

        Args:
            ro_repos: Read-only repositories
            uow_factory: Unit of work factory for creating write transactions
            user_id: User ID for scoping
            get_llm_prompt_context_handler: Handler for prompt context
            pubsub_gateway: Gateway for publishing kiosk notifications to Redis
        """
        super().__init__(ro_repos, uow_factory, user_id)
        self._get_llm_prompt_context_handler = get_llm_prompt_context_handler
        self.pubsub_gateway = pubsub_gateway
        self._triggered_by: str | None = None

    async def handle(self, command: KioskNotificationCommand) -> None:
        """Evaluate day context and send kiosk notification if warranted.

        Args:
            command: The command containing user_id and trigger info
        """
        # Check if kiosk notifications are enabled
        if not settings.SMART_NOTIFICATIONS_ENABLED:
            logger.debug("Kiosk notifications are disabled (using SMART_NOTIFICATIONS_ENABLED setting)")
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

        async def decide_kiosk_notification(
            should_notify: bool,
            message: str | None = None,
            category: Literal[
                "calendar_event",
                "routine",
                "task_reminder",
                "time_block_change",
                "other",
            ]
            | None = None,
            reason: str | None = None,
        ) -> None:
            """Send a kiosk notification if warranted.

            This will be read out loud on the kiosk display.
            """
            if not should_notify:
                logger.debug(
                    "LLM decided not to send kiosk notification for user %s",
                    self.user_id,
                )
                return None

            if not message:
                logger.warning(
                    "LLM decided to notify but provided no message for user %s",
                    self.user_id,
                )
                return None

            decision = KioskNotificationDecision(
                message=message,
                category=category or "other",
                reason=reason,
            )

            # Create message hash for de-duplication
            message_hash = hashlib.sha256(decision.message.encode("utf-8")).hexdigest()

            # Build payload for kiosk notification
            payload = {
                "type": "kiosk_notification",
                "message": decision.message,
                "category": decision.category,
                "message_hash": message_hash,
                "created_at": datetime.now(UTC).isoformat(),
                "triggered_by": self._triggered_by,
            }

            try:
                # Publish to Redis channel for kiosk WebSocket clients
                await self.pubsub_gateway.publish_to_user_channel(
                    user_id=self.user_id,
                    channel_type="kiosk-notifications",
                    message=payload,
                )
                logger.info(
                    "Published kiosk notification to user %s: %s",
                    self.user_id,
                    decision.message[:50],
                )
            except Exception as exc:  # pylint: disable=broad-except
                logger.error(
                    "Failed to publish kiosk notification for user %s: %s",
                    self.user_id,
                    exc,
                )
                logger.exception(exc)
            return None

        return [
            LLMTool(
                name="decide_kiosk_notification",
                callback=decide_kiosk_notification,
                description="Decide whether to send a kiosk notification that will be read out loud.",
            )
        ]
