"""Command to run the this_month_status LLM use case and persist a check-in."""

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
class ThisMonthsStatusCommand(Command):
    """Command to run this_month_status use case and persist an LLM-generated check-in."""


class ThisMonthsStatusAssessment(BaseModel):
    """Validated assessment payload returned by this_month_status."""

    text: str | None = None
    scores: dict[str, float | int] = Field(default_factory=dict)


class ThisMonthsStatusHandler(
    LLMHandlerMixin, BaseCommandHandler[ThisMonthsStatusCommand, None]
):
    """Runs this_month_status LLM use case and persists a UserCheckIn with source=llm_use_case, source_name=this_month_status."""

    get_llm_prompt_context_handler: GetLLMPromptContextHandler
    user_check_in_ro_repo: UserCheckInRepositoryReadOnlyProtocol
    name = "this_month_status"
    template_usecase = "this_month_status"

    async def handle(self, command: ThisMonthsStatusCommand) -> None:
        """Run LLM and persist check-in from validated assessment output."""
        _ = command
        result = await self.run_assessment_llm(ThisMonthsStatusAssessment)
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
            source_name="this_month_status",
            source_metadata={
                "llm_provider": result.llm_provider.value,
                "usecase": "this_month_status",
            },
            checkin_at=result.current_time,
            text=assessment.text.strip() if assessment.text and assessment.text.strip() else None,
            scores=scores_clean,
        )
        entity.create()
        async with self._uow_factory.create(self.user) as uow:
            await uow.create(entity)
        logger.info(f"Persisted this_month_status check-in for user {self.user.id}")

    async def build_prompt_input(self, date: dt_date) -> UseCasePromptInput:
        """Build prompt with today's context and last 30 days of check-ins."""
        prompt_context = await self.get_llm_prompt_context_handler.handle(
            GetLLMPromptContextQuery(date=date)
        )
        window_start = datetime.now(UTC) - timedelta(days=30)
        recent = await self.user_check_in_ro_repo.search(
            value_objects.UserCheckInQuery(
                checkin_at_after=window_start,
                order_by="checkin_at",
                order_by_desc=True,
                limit=200,
            )
        )
        return UseCasePromptInput(
            prompt_context=prompt_context,
            extra_template_vars={"recent_check_ins": recent},
        )

