"""LLM use case for smart notifications."""

from __future__ import annotations

from typing import TYPE_CHECKING

from lykke.application.queries.get_llm_prompt_context import (
    GetLLMPromptContextHandler,
    GetLLMPromptContextQuery,
)

from .base import BaseUseCase

if TYPE_CHECKING:
    from datetime import date as datetime_date

    from lykke.domain import value_objects


class NotificationUseCase(BaseUseCase):
    """Use case for evaluating smart notifications."""

    name = "notification"
    template_usecase = "notification"

    def __init__(
        self, get_llm_prompt_context_handler: GetLLMPromptContextHandler
    ) -> None:
        self._get_llm_prompt_context_handler = get_llm_prompt_context_handler

    async def build_prompt_context(
        self, date: datetime_date
    ) -> value_objects.LLMPromptContext:
        return await self._get_llm_prompt_context_handler.handle(
            GetLLMPromptContextQuery(date=date)
        )
