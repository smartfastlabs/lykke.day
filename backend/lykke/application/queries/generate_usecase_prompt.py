"""Query to generate LLM prompt parts for a use case."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.unit_of_work import ReadOnlyRepositories
from lykke.core.utils.templates import render_for_user
from lykke.domain import value_objects


@dataclass(frozen=True)
class GenerateUseCasePromptQuery(Query):
    """Query to generate LLM prompt parts for a use case."""

    usecase: str
    prompt_context: value_objects.LLMPromptContext | None = None
    current_time: datetime | None = None
    include_context: bool = True
    include_ask: bool = True


@dataclass(frozen=True)
class UseCasePromptResult:
    """Rendered prompt parts for a use case."""

    system_prompt: str
    context_prompt: str | None = None
    ask_prompt: str | None = None


class GenerateUseCasePromptHandler(
    BaseQueryHandler[GenerateUseCasePromptQuery, UseCasePromptResult]
):
    """Generate LLM prompt parts for a use case."""

    async def handle(self, query: GenerateUseCasePromptQuery) -> UseCasePromptResult:
        """Handle the prompt generation query."""
        user_amendments = await self._get_user_amendments(query.usecase)
        system_prompt = render_for_user(
            query.usecase,
            "system",
            user_amendments=user_amendments,
        )

        context_prompt: str | None = None
        if query.include_context:
            if query.prompt_context is None or query.current_time is None:
                raise ValueError(
                    "prompt_context and current_time are required when include_context is True"
                )
            context_prompt = render_for_user(
                query.usecase,
                "context",
                context=query.prompt_context,
                current_time=query.current_time,
            )

        ask_prompt: str | None = None
        if query.include_ask:
            ask_prompt = render_for_user(query.usecase, "ask")

        return UseCasePromptResult(
            system_prompt=system_prompt,
            context_prompt=context_prompt,
            ask_prompt=ask_prompt,
        )

    async def _get_user_amendments(self, usecase: str) -> list[str]:
        """Fetch user amendments for the given usecase."""
        configs = await self.usecase_config_ro_repo.search(
            value_objects.UseCaseConfigQuery(usecase=usecase)
        )
        if not configs:
            return []

        config = configs[0].config
        user_amendments = config.get("user_amendments", [])
        if isinstance(user_amendments, list):
            return user_amendments
        return []
