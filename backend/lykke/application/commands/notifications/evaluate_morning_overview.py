"""Command to evaluate and send morning overview notifications."""

import hashlib
import json
from dataclasses import dataclass
from datetime import date as dt_date, datetime
from typing import Any, Literal
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
from lykke.application.queries.compute_task_risk import (
    ComputeTaskRiskHandler,
    ComputeTaskRiskQuery,
)
from lykke.application.queries.get_llm_prompt_context import (
    GetLLMPromptContextHandler,
    GetLLMPromptContextQuery,
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


class MorningOverviewHandler(
    LLMHandlerMixin, BaseCommandHandler[MorningOverviewCommand, None]
):
    """Evaluates day context using LLM and sends morning overview if warranted."""

    push_subscription_ro_repo: PushSubscriptionRepositoryReadOnlyProtocol
    user_ro_repo: UserRepositoryReadOnlyProtocol
    name = "morning_overview"
    template_usecase = "morning_overview"

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        get_llm_prompt_context_handler: GetLLMPromptContextHandler,
        compute_task_risk_handler: ComputeTaskRiskHandler,
        send_push_notification_handler: SendPushNotificationHandler,
    ) -> None:
        """Initialize MorningOverviewHandler.

        Args:
            ro_repos: Read-only repositories
            uow_factory: Unit of work factory for creating write transactions
            user_id: User ID for scoping
            get_llm_prompt_context_handler: Handler for prompt context
            compute_task_risk_handler: Handler for task risk scoring
            send_push_notification_handler: Handler for sending push notifications
        """
        super().__init__(ro_repos, uow_factory, user_id)
        self._get_llm_prompt_context_handler = get_llm_prompt_context_handler
        self._compute_task_risk_handler = compute_task_risk_handler
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
            user = await self.user_ro_repo.get(self.user_id)
        except Exception as e:
            logger.error(f"Failed to load user {self.user_id}: {e}")
            return

        # Check if user has LLM provider configured
        if not user.settings or not user.settings.llm_provider:
            logger.debug(
                f"User {self.user_id} has no LLM provider configured, skipping"
            )
            return

        # Check if user has morning overview time configured
        if not user.settings.morning_overview_time:
            logger.debug(
                f"User {self.user_id} has no morning overview time configured, skipping"
            )
            return

        await self.run_llm()

    async def build_prompt_input(self, date: dt_date) -> UseCasePromptInput:
        prompt_context = await self._get_llm_prompt_context_handler.handle(
            GetLLMPromptContextQuery(date=date)
        )
        risk_result = await self._compute_task_risk_handler.handle(
            ComputeTaskRiskQuery(tasks=prompt_context.tasks)
        )
        high_risk_tasks: list[dict[str, Any]] = []
        risk_scores_by_task_id = {
            risk.task_id: risk for risk in risk_result.high_risk_tasks
        }
        for task in prompt_context.tasks:
            if task.id in risk_scores_by_task_id:
                risk_score = risk_scores_by_task_id[task.id]
                high_risk_tasks.append(
                    {
                        "name": task.name,
                        "status": task.status,
                        "frequency": task.frequency,
                        "tags": task.tags,
                        "completion_rate": round(risk_score.completion_rate, 1),
                        "risk_reason": risk_score.risk_reason,
                    }
                )
        return UseCasePromptInput(
            prompt_context=prompt_context,
            extra_template_vars={"high_risk_tasks": high_risk_tasks},
        )

    def build_tools(
        self,
        *,
        current_time: datetime,
        prompt_context: value_objects.LLMPromptContext,
        llm_provider: value_objects.LLMProvider,
    ) -> list[LLMTool]:
        async def decide_morning_overview(
            should_notify: bool,
            message: str | None = None,
            priority: Literal["high", "medium", "low"] | None = None,
            reason: str | None = None,
        ) -> None:
            """Send a morning overview notification if warranted."""
            if not should_notify:
                logger.debug(
                    "LLM decided not to send morning overview for user %s",
                    self.user_id,
                )
                return None
            decision = value_objects.NotificationDecision(
                message=message or "",
                priority=priority or "medium",
                reason=reason,
            )

            day_context_snapshot = serialize_day_context(prompt_context, current_time)
            message_hash = hashlib.sha256(decision.message.encode("utf-8")).hexdigest()
            payload = build_notification_payload_for_smart_notification(decision)
            content_dict = dataclass_to_json_dict(payload)
            filtered_content = {k: v for k, v in content_dict.items() if v is not None}
            content_str = json.dumps(filtered_content)

            try:
                subscriptions = await self.push_subscription_ro_repo.all()
                if not subscriptions:
                    logger.debug(
                        "No push subscriptions found for user %s",
                        self.user_id,
                    )
                    async with self._uow_factory.create(self.user_id) as uow:
                        notification = PushNotificationEntity(
                            user_id=self.user_id,
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
                            llm_provider=llm_provider.value,
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
                        reason=decision.reason,
                        day_context_snapshot=day_context_snapshot,
                        message_hash=message_hash,
                        triggered_by="morning_overview",
                        llm_provider=llm_provider.value,
                    )
                )
                logger.info(
                    "Sent morning overview to %s subscription(s) for user %s",
                    len(subscriptions),
                    self.user_id,
                )
            except Exception as exc:  # pylint: disable=broad-except
                logger.error(
                    "Failed to send morning overview for user %s: %s",
                    self.user_id,
                    exc,
                )
                logger.exception(exc)
            return None

        return [
            LLMTool(
                name="decide_morning_overview",
                callback=decide_morning_overview,
                description="Decide whether to send a morning overview.",
            )
        ]
