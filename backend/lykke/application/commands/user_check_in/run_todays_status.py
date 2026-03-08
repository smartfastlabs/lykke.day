"""Command to run the todays_status LLM use case and persist a check-in."""

from dataclasses import dataclass
from datetime import UTC, date as dt_date, datetime, timedelta
from typing import Any

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.gateways.llm_gateway_factory_protocol import (
    LLMGatewayFactoryProtocol,
)
from lykke.application.gateways.llm_protocol import LLMTool
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


@dataclass(frozen=True)
class TodaysStatusCommand(Command):
    """Command to run todays_status use case and persist an LLM-generated check-in."""

    pass


class TodaysStatusHandler(
    LLMHandlerMixin, BaseCommandHandler[TodaysStatusCommand, None]
):
    """Runs todays_status LLM use case and persists a UserCheckIn with source=llm_use_case, source_name=todays_status."""

    get_llm_prompt_context_handler: GetLLMPromptContextHandler
    user_check_in_ro_repo: UserCheckInRepositoryReadOnlyProtocol
    name = "todays_status"
    template_usecase = "todays_status"

    async def handle(self, command: TodaysStatusCommand) -> None:
        """Run LLM and persist check-in if the model calls the tool."""
        result = await self.run_llm()
        if result is None:
            return
        logger.debug(
            f"todays_status completed for user {self.user.id}, "
            f"tool_results={len(result.tool_results)}"
        )

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

    def build_tools(
        self,
        *,
        current_time: datetime,
        prompt_context: value_objects.LLMPromptContext,
        llm_provider: value_objects.LLMProvider,
    ) -> list[LLMTool]:
        """Single tool: record_todays_status(text=None, scores=None)."""

        async def record_todays_status(
            text: str | None = None,
            scores: dict[str, float] | None = None,
        ) -> None:
            """Record today's status check-in from the LLM."""
            scores = scores or {}
            # Coerce to plain dict with numeric values for storage
            scores_clean: dict[str, Any] = {}
            for k, v in (scores or {}).items():
                if isinstance(k, str) and v is not None:
                    try:
                        scores_clean[k] = float(v) if not isinstance(v, (int, float)) else v
                    except (TypeError, ValueError):
                        continue
            entity = UserCheckInEntity(
                user_id=self.user.id,
                source=value_objects.UserCheckInSource.LLM_USE_CASE,
                source_name="todays_status",
                source_metadata={
                    "llm_provider": llm_provider.value,
                    "usecase": "todays_status",
                },
                checkin_at=current_time,
                text=text.strip() if text and text.strip() else None,
                scores=scores_clean,
            )
            entity.create()
            async with self._uow_factory.create(self.user) as uow:
                await uow.create(entity)
            logger.info(
                f"Persisted todays_status check-in for user {self.user.id}"
            )

        return [LLMTool(callback=record_todays_status)]
