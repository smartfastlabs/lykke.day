"""LLM use case for morning overview notifications."""

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


class MorningOverviewUseCase(BaseUseCase):
    """Use case for generating morning overview notifications."""

    name = "morning_overview"
    template_usecase = "morning_overview"

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
