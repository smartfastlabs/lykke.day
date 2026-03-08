"""Shared handler logic for LLM-generated user check-ins."""

from __future__ import annotations

from datetime import UTC, date as dt_date, datetime, timedelta
from typing import Generic, TypeVar

from loguru import logger
from pydantic import BaseModel, Field

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.llm import LLMHandlerMixin, UseCasePromptInput
from lykke.application.queries.get_llm_prompt_context import (
    GetLLMPromptContextHandler,
    GetLLMPromptContextQuery,
)
from lykke.application.repositories import UserCheckInRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import UserCheckInEntity

CommandT = TypeVar("CommandT", bound=Command)


class StatusAssessment(BaseModel):
    """Validated status assessment payload returned by LLM use cases."""

    text: str | None = None
    scores: dict[str, float | int] = Field(default_factory=dict)


class BaseLLMUserCheckInHandler(
    LLMHandlerMixin, BaseCommandHandler[CommandT, None], Generic[CommandT]
):
    """Shared implementation for daily/weekly/monthly LLM check-in handlers."""

    get_llm_prompt_context_handler: GetLLMPromptContextHandler
    user_check_in_ro_repo: UserCheckInRepositoryReadOnlyProtocol

    # Subclasses must override these.
    recent_checkin_window_days: int = 0
    recent_checkin_limit: int = 0
    assessment_model: type[BaseModel] = StatusAssessment

    async def handle(self, command: CommandT) -> None:
        """Run assessment LLM and persist a normalized check-in."""
        _ = command
        result = await self.run_assessment_llm(self.assessment_model)
        if result is None:
            return

        assessment = result.assessment
        raw_scores = getattr(assessment, "scores", None)
        raw_text = getattr(assessment, "text", None)
        scores_clean = self._normalize_scores(raw_scores)

        entity = UserCheckInEntity(
            user_id=self.user.id,
            source=value_objects.UserCheckInSource.LLM_USE_CASE,
            source_name=self.template_usecase,
            source_metadata={
                "llm_provider": result.llm_provider.value,
                "usecase": self.template_usecase,
            },
            checkin_at=result.current_time,
            text=raw_text.strip() if isinstance(raw_text, str) and raw_text.strip() else None,
            scores=scores_clean,
        )

        async with self.new_uow() as uow:
            await uow.create(entity)

        logger.info(f"Persisted {self.template_usecase} check-in for user {self.user.id}")

    async def build_prompt_input(self, date: dt_date) -> UseCasePromptInput:
        """Build prompt input with recent check-ins for continuity."""
        prompt_context = await self.get_llm_prompt_context_handler.handle(
            GetLLMPromptContextQuery(date=date)
        )
        window_start = datetime.now(UTC) - timedelta(days=self.recent_checkin_window_days)
        recent = await self.user_check_in_ro_repo.search(
            value_objects.UserCheckInQuery(
                checkin_at_after=window_start,
                order_by="checkin_at",
                order_by_desc=True,
                limit=self.recent_checkin_limit,
            )
        )
        return UseCasePromptInput(
            prompt_context=prompt_context,
            extra_template_vars={"recent_check_ins": recent},
        )

    @staticmethod
    def _normalize_scores(scores: object) -> dict[str, float]:
        """Normalize score payload into numeric values only."""
        if not isinstance(scores, dict):
            return {}

        cleaned: dict[str, float] = {}
        for key, value in scores.items():
            if not isinstance(key, str) or value is None:
                continue
            try:
                cleaned[key] = float(value)
            except (TypeError, ValueError):
                continue
        return cleaned
