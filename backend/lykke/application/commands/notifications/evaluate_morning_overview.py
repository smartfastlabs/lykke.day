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
from lykke.application.gateways.llm_gateway_factory_protocol import (
    LLMGatewayFactoryProtocol,
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
from lykke.core.utils.llm_snapshot import build_referenced_entities
from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.entities import PushNotificationEntity, UserEntity


@dataclass(frozen=True)
class MorningOverviewCommand(Command):
    """Command to evaluate day context and send morning overview if warranted."""

    user: UserEntity


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
        user: UserEntity,
        llm_gateway_factory: LLMGatewayFactoryProtocol,
        get_llm_prompt_context_handler: GetLLMPromptContextHandler,
        compute_task_risk_handler: ComputeTaskRiskHandler,
        send_push_notification_handler: SendPushNotificationHandler,
    ) -> None:
        """Initialize MorningOverviewHandler.

        Args:
            ro_repos: Read-only repositories
            uow_factory: Unit of work factory for creating write transactions
            user: User entity for scoping
            get_llm_prompt_context_handler: Handler for prompt context
            compute_task_risk_handler: Handler for task risk scoring
            send_push_notification_handler: Handler for sending push notifications
        """
        super().__init__(ro_repos, uow_factory, user)
        self._llm_gateway_factory = llm_gateway_factory
        self._get_llm_prompt_context_handler = get_llm_prompt_context_handler
        self._compute_task_risk_handler = compute_task_risk_handler
        self._send_push_notification_handler = send_push_notification_handler

    async def handle(self, command: MorningOverviewCommand) -> None:
        """Evaluate day context and send morning overview if warranted.

        Args:
            command: The command containing user
        """
        # Check if smart notifications are enabled
        if not settings.SMART_NOTIFICATIONS_ENABLED:
            logger.debug("Smart notifications are disabled")
            return

        # Load user to get LLM provider preference
        user = self.user

        # Check if user has LLM provider configured
        if not user.settings or not user.settings.llm_provider:
            logger.debug(
                f"User {self.user.id} has no LLM provider configured, skipping"
            )
            return

        # Check if user has morning overview time configured
        if not user.settings.morning_overview_time:
            logger.debug(
                f"User {self.user.id} has no morning overview time configured, skipping"
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
        def build_llm_snapshot(
            *,
            tool_name: str,
            tool_args: dict[str, Any],
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

        async def decide_morning_overview(
            should_notify: bool,
            message: str | None = None,
            priority: Literal["high", "medium", "low"] | None = None,
            reason: str | None = None,
        ) -> None:
            """Decide whether to send a morning overview."""
            if not should_notify:
                logger.debug(
                    f"LLM decided not to send morning overview for user {self.user.id}",
                )
                return None
            decision = value_objects.NotificationDecision(
                message=message or "",
                priority=priority or "medium",
                reason=reason,
            )

            llm_snapshot = build_llm_snapshot(
                tool_name="decide_morning_overview",
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
            content_str = json.dumps(filtered_content)

            try:
                subscriptions = await self.push_subscription_ro_repo.all()
                if not subscriptions:
                    logger.debug(
                        f"No push subscriptions found for user {self.user.id}",
                    )
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
                            triggered_by="morning_overview",
                            llm_snapshot=llm_snapshot,
                            referenced_entities=(
                                llm_snapshot.referenced_entities if llm_snapshot else []
                            ),
                        )
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
                        triggered_by="morning_overview",
                        llm_snapshot=llm_snapshot,
                        referenced_entities=(
                            llm_snapshot.referenced_entities if llm_snapshot else None
                        ),
                    )
                )
                logger.info(
                    f"Sent morning overview to {len(subscriptions)} subscription(s) for user {self.user.id}",
                )
            except Exception as exc:  # pylint: disable=broad-except
                logger.error(
                    f"Failed to send morning overview for user {self.user.id}: {exc}",
                )
                logger.exception(exc)
            return None

        return [LLMTool(callback=decide_morning_overview)]
