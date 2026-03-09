"""Command to run the user_status_use_case LLM use case and persist a check-in."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date as dt_date, datetime, timedelta

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


@dataclass(frozen=True)
class UserStatusUseCaseCommand(Command):
    """Command to run user_status_use_case and persist an LLM-generated check-in."""


class UserStatusUseCaseAssessment(BaseModel):
    """Validated status assessment payload returned by this use case."""

    text: str | None = None
    scores: dict[str, float | int] = Field(default_factory=dict)


@dataclass(frozen=True)
class GeneratedUserStatusCheckIn:
    """Normalized generated check-in payload."""

    text: str | None
    scores: dict[str, float]


class UserStatusUseCaseHandler(
    LLMHandlerMixin, BaseCommandHandler[UserStatusUseCaseCommand, None]
):
    """Runs user_status_use_case and persists a normalized UserCheckIn."""

    get_llm_prompt_context_handler: GetLLMPromptContextHandler
    user_check_in_ro_repo: UserCheckInRepositoryReadOnlyProtocol

    name = "user_status_use_case"
    template_usecase = "user_status_use_case"
    recent_checkin_window_days = 3
    recent_checkin_limit = 20
    assessment_model = UserStatusUseCaseAssessment

    async def handle(self, command: UserStatusUseCaseCommand) -> None:
        """Run assessment LLM and persist the resulting check-in."""
        _ = command
        result = await self.run_assessment_llm(self.assessment_model)
        if result is None:
            return

        generated = self._normalize_assessment(result.assessment)

        entity = UserCheckInEntity(
            user_id=self.user.id,
            source=value_objects.UserCheckInSource.LLM_USE_CASE,
            source_name=self.template_usecase,
            source_metadata={
                "llm_provider": result.llm_provider.value,
                "usecase": self.template_usecase,
            },
            checkin_at=result.current_time,
            text=generated.text,
            scores=generated.scores,
        )

        async with self.new_uow() as uow:
            await uow.create(entity)

        logger.info(
            f"Persisted {self.template_usecase} check-in for user {self.user.id}"
        )

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
        status_signals = self._status_signals_for_prompt()
        return UseCasePromptInput(
            prompt_context=prompt_context,
            extra_template_vars={
                "recent_check_ins": recent,
                "status_signals": status_signals,
            },
        )

    async def preview_generated_checkin(self) -> GeneratedUserStatusCheckIn | None:
        """Run the usecase and return normalized check-in payload without persisting."""
        result = await self.run_assessment_llm(self.assessment_model)
        if result is None:
            return None
        return self._normalize_assessment(result.assessment)

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

    def _status_signals_for_prompt(self) -> list[dict[str, object]]:
        if not self.user.settings or not self.user.settings.status_signals:
            return []
        return [
            {
                "name": signal.name,
                "slug": signal.slug,
                "description": signal.description,
                "goal": {
                    "text": signal.goal.text,
                    "value": signal.goal.value,
                },
            }
            for signal in self.user.settings.status_signals
        ]

    def _normalize_assessment(self, assessment: object) -> GeneratedUserStatusCheckIn:
        raw_scores = getattr(assessment, "scores", None)
        raw_text = getattr(assessment, "text", None)
        return GeneratedUserStatusCheckIn(
            text=raw_text.strip() if isinstance(raw_text, str) and raw_text.strip() else None,
            scores=self._normalize_scores(raw_scores),
        )
