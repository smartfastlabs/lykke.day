"""LLM use case for morning overview notifications."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from lykke.application.gateways.llm_protocol import LLMTool
from lykke.application.queries.get_llm_prompt_context import (
    GetLLMPromptContextHandler,
    GetLLMPromptContextQuery,
)
from lykke.application.queries.compute_task_risk import (
    ComputeTaskRiskHandler,
    ComputeTaskRiskQuery,
)
from lykke.domain import value_objects

from .base import BaseUseCase, UseCasePromptInput

if TYPE_CHECKING:
    from datetime import date as datetime_date

    from lykke.domain import value_objects


class MorningOverviewUseCase(BaseUseCase):
    """Use case for generating morning overview notifications."""

    name = "morning_overview"
    template_usecase = "morning_overview"

    def __init__(
        self,
        get_llm_prompt_context_handler: GetLLMPromptContextHandler,
        compute_task_risk_handler: ComputeTaskRiskHandler,
    ) -> None:
        self._get_llm_prompt_context_handler = get_llm_prompt_context_handler
        self._compute_task_risk_handler = compute_task_risk_handler

    async def build_prompt_input(self, date: datetime_date) -> UseCasePromptInput:
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
    ) -> list[LLMTool]:
        def decide_morning_overview(
            should_notify: bool,
            message: str | None = None,
            priority: Literal["high", "medium", "low"] | None = None,
            reason: str | None = None,
        ) -> value_objects.NotificationDecision | None:
            """Return the morning overview decision."""
            if not should_notify:
                return None
            return value_objects.NotificationDecision(
                message=message or "",
                priority=priority or "medium",
                reason=reason,
            )

        return [
            LLMTool(
                name="decide_morning_overview",
                callback=decide_morning_overview,
                description="Decide whether to send a morning overview.",
            )
        ]
