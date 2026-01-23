"""Command to evaluate and send morning overview notifications."""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from loguru import logger
from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.commands.push_subscription import (
    SendPushNotificationCommand,
    SendPushNotificationHandler,
)
from lykke.application.gateways.llm_gateway_factory import LLMGatewayFactory
from lykke.application.llm_usecases import MorningOverviewUseCase
from lykke.application.notifications import (
    build_notification_payload_for_smart_notification,
)
from lykke.application.queries import (
    ComputeTaskRiskHandler,
    ComputeTaskRiskQuery,
    GenerateUseCasePromptHandler,
    GenerateUseCasePromptQuery,
    GetLLMPromptContextHandler,
)
from lykke.application.repositories import (
    PushSubscriptionRepositoryReadOnlyProtocol,
    UserRepositoryReadOnlyProtocol,
)
from lykke.application.unit_of_work import ReadOnlyRepositories, UnitOfWorkFactory
from lykke.core.config import settings
from lykke.core.exceptions import DomainError
from lykke.core.utils.dates import get_current_date, get_current_datetime_in_timezone
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
        get_llm_prompt_context_handler: GetLLMPromptContextHandler,
        compute_task_risk_handler: ComputeTaskRiskHandler,
        generate_usecase_prompt_handler: GenerateUseCasePromptHandler,
        send_push_notification_handler: SendPushNotificationHandler,
    ) -> None:
        """Initialize MorningOverviewHandler.

        Args:
            ro_repos: Read-only repositories
            uow_factory: Unit of work factory for creating write transactions
            user_id: User ID for scoping
            get_llm_prompt_context_handler: Handler for loading LLM prompt context
            compute_task_risk_handler: Handler for computing task risk
            generate_usecase_prompt_handler: Handler for generating use case prompts
            send_push_notification_handler: Handler for sending push notifications
        """
        super().__init__(ro_repos, uow_factory, user_id)
        self._get_llm_prompt_context_handler = get_llm_prompt_context_handler
        self._compute_task_risk_handler = compute_task_risk_handler
        self._generate_usecase_prompt_handler = generate_usecase_prompt_handler
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

        llm_provider = user.settings.llm_provider

        try:
            today = get_current_date(user.settings.timezone)
            usecase = MorningOverviewUseCase(
                get_llm_prompt_context_handler=self._get_llm_prompt_context_handler
            )
            prompt_context = await usecase.build_prompt_context(today)
        except Exception as e:
            logger.error(
                f"Failed to load LLM prompt context for user {command.user_id}: {e}"
            )
            return

        # Compute risk scores for tasks
        risk_result = await self._compute_task_risk_handler.handle(
            ComputeTaskRiskQuery(tasks=prompt_context.tasks)
        )

        # Build high_risk_tasks list for template (map risk scores to tasks)
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
                        "status": task.status,  # Keep as enum for template access
                        "frequency": task.frequency,  # Keep as enum for template access
                        "tags": task.tags,
                        "completion_rate": round(risk_score.completion_rate, 1),
                        "risk_reason": risk_score.risk_reason,
                    }
                )

        # Serialize day context for storage
        current_time = get_current_datetime_in_timezone(user.settings.timezone)

        # Generate prompts for LLM
        prompt_result = await self._generate_usecase_prompt_handler.handle(
            GenerateUseCasePromptQuery(
                usecase=usecase.template_usecase,
                prompt_context=prompt_context,
                current_time=current_time,
                include_context=True,
                include_ask=True,
                extra_template_vars={"high_risk_tasks": high_risk_tasks},
            )
        )
        if prompt_result.context_prompt is None or prompt_result.ask_prompt is None:
            raise RuntimeError("Prompt generation did not include all prompt parts")

        system_prompt = prompt_result.system_prompt
        context_prompt = prompt_result.context_prompt
        ask_prompt = prompt_result.ask_prompt

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
                f"LLM decided not to send morning overview for user {command.user_id}"
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
                        triggered_by="morning_overview",
                        llm_provider=llm_provider.value,
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
                    llm_provider=llm_provider.value,
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
