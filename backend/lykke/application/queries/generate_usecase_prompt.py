"""Query to generate LLM prompt parts for a use case."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from lykke.application.queries.base import BaseQueryHandler, Query
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
    extra_template_vars: dict[str, Any] | None = None


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
        user = await self.user_ro_repo.get(self.user_id)
        user_amendments = await self._get_user_amendments(query.usecase)
        base_personality_slug = user.settings.base_personality_slug
        llm_personality_amendments = user.settings.llm_personality_amendments
        system_prompt = render_for_user(
            query.usecase,
            "system",
            user_amendments=user_amendments,
            base_personality_slug=base_personality_slug,
            llm_personality_amendments=llm_personality_amendments,
        )

        context_prompt: str | None = None
        if query.include_context:
            if query.prompt_context is None or query.current_time is None:
                raise ValueError(
                    "prompt_context and current_time are required when include_context is True"
                )
            template_vars: dict[str, Any] = {
                "context": query.prompt_context,
                "current_time": query.current_time,
            }
            if query.extra_template_vars:
                template_vars.update(query.extra_template_vars)
            context_prompt = render_for_user(
                query.usecase,
                "context",
                **template_vars,
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
