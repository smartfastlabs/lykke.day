"""LLM use case for smart notifications."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal

from lykke.application.gateways.llm_protocol import LLMTool
from lykke.application.queries.get_llm_prompt_context import (
    GetLLMPromptContextHandler,
    GetLLMPromptContextQuery,
)
from lykke.domain import value_objects

from .base import BaseUseCase, UseCasePromptInput

if TYPE_CHECKING:
    from datetime import date as datetime_date


class NotificationUseCase(BaseUseCase):
    """Use case for evaluating smart notifications."""

    name = "notification"
    template_usecase = "notification"

    def __init__(
        self, get_llm_prompt_context_handler: GetLLMPromptContextHandler
    ) -> None:
        self._get_llm_prompt_context_handler = get_llm_prompt_context_handler

    async def build_prompt_input(self, date: datetime_date) -> UseCasePromptInput:
        prompt_context = await self._get_llm_prompt_context_handler.handle(
            GetLLMPromptContextQuery(date=date)
        )
        return UseCasePromptInput(prompt_context=prompt_context)

    def build_tools(
        self,
        *,
        current_time: datetime,
        prompt_context: value_objects.LLMPromptContext,
    ) -> list[LLMTool]:
        def decide_notification(
            should_notify: bool,
            message: str | None = None,
            priority: Literal["high", "medium", "low"] | None = None,
            reason: str | None = None,
        ) -> value_objects.NotificationDecision | None:
            """Return the notification decision."""
            if not should_notify:
                return None
            return value_objects.NotificationDecision(
                message=message or "",
                priority=priority or "medium",
                reason=reason,
            )

        return [
            LLMTool(
                name="decide_notification",
                callback=decide_notification,
                description="Decide whether to send a smart notification.",
            )
        ]
