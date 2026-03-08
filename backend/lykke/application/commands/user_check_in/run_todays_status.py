"""Command to run the todays_status LLM use case and persist a check-in."""

from dataclasses import dataclass
from datetime import UTC, date as dt_date, datetime, timedelta
from typing import Any

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.llm import LLMHandlerMixin, UseCasePromptInput
from lykke.application.queries.get_llm_prompt_context import (
    GetLLMPromptContextHandler,
    GetLLMPromptContextQuery,
)
from lykke.application.repositories import (
    UserCheckInRepositoryReadOnlyProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import UserCheckInEntity
from pydantic import BaseModel, Field


@dataclass(frozen=True)
class TodaysStatusCommand(Command):
    """Command to run todays_status use case and persist an LLM-generated check-in."""


class TodaysStatusAssessment(BaseModel):
    """Validated assessment payload returned by todays_status."""

    text: str | None = None
    scores: dict[str, float | int] = Field(default_factory=dict)


class TodaysStatusHandler(
    LLMHandlerMixin, BaseCommandHandler[TodaysStatusCommand, None]
):
    """Runs todays_status LLM use case and persists a UserCheckIn with source=llm_use_case, source_name=todays_status."""

    get_llm_prompt_context_handler: GetLLMPromptContextHandler
    user_check_in_ro_repo: UserCheckInRepositoryReadOnlyProtocol
    name = "todays_status"
    template_usecase = "todays_status"

    async def handle(self, command: TodaysStatusCommand) -> None:
        """Run LLM and persist check-in from validated assessment output."""
        _ = command
        result = await self.run_assessment_llm(TodaysStatusAssessment)
        if result is None:
            return
        assessment = result.assessment
        scores_clean: dict[str, Any] = {}
        for k, v in (assessment.scores or {}).items():
            if isinstance(k, str) and v is not None:
                try:
                    scores_clean[k] = float(v)
                except (TypeError, ValueError):
                    continue
        entity = UserCheckInEntity(
            user_id=self.user.id,
            source=value_objects.UserCheckInSource.LLM_USE_CASE,
            source_name="todays_status",
            source_metadata={
                "llm_provider": result.llm_provider.value,
                "usecase": "todays_status",
            },
            checkin_at=result.current_time,
            text=assessment.text.strip() if assessment.text and assessment.text.strip() else None,
            scores=scores_clean,
        )
        entity.create()
        async with self._uow_factory.create(self.user) as uow:
            await uow.create(entity)
        logger.info(f"Persisted todays_status check-in for user {self.user.id}")

    async def build_prompt_input(self, date: dt_date) -> UseCasePromptInput:
        """Build prompt with today's day context and recent check-ins."""
        prompt_context = await self.get_llm_prompt_context_handler.handle(
            GetLLMPromptContextQuery(date=date)
        )
        # Recent check-ins (last 3 days) for continuity
        window_start = datetime.now(UTC) - timedelta(days=3)
        recent = await self.user_check_in_ro_repo.search(
            value_objects.UserCheckInQuery(
                checkin_at_after=window_start,
                order_by="checkin_at",
                order_by_desc=True,
                limit=20,
            )
        )
        return UseCasePromptInput(
            prompt_context=prompt_context,
            extra_template_vars={"recent_check_ins": recent},
        )

