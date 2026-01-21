"""Query to preview rendered templates with user context."""
from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.queries.get_day_context import GetDayContextHandler
from lykke.application.queries.get_llm_prompt_context import (
    GetLLMPromptContextHandler,
    GetLLMPromptContextQuery,
)
from lykke.application.repositories import TemplateRepositoryReadOnlyProtocol
from lykke.core.utils.day_context_serialization import serialize_day_context
from lykke.core.utils.templates import render_for_user
from lykke.domain.value_objects import LLMPromptContext
from lykke.core.utils.dates import get_current_date, get_current_datetime_in_timezone


@dataclass(frozen=True)
class PreviewTemplateQuery(Query):
    """Query to preview a template set for a use case."""

    usecase: str


@dataclass(frozen=True)
class PreviewTemplateResult:
    """Rendered template preview result."""

    system_prompt: str
    context_prompt: str
    ask_prompt: str
    context_data: dict


class PreviewTemplateHandler(
    BaseQueryHandler[PreviewTemplateQuery, PreviewTemplateResult]
):
    """Render templates using the user's current context."""

    template_ro_repo: TemplateRepositoryReadOnlyProtocol

    async def handle(self, query: PreviewTemplateQuery) -> PreviewTemplateResult:
        """Render system + context + ask prompts for the given use case."""
        try:
            user = await self.user_ro_repo.get(self.user_id)
            timezone = user.settings.timezone
        except Exception:
            timezone = None
        day_context = await self._get_today_context(timezone)
        current_time = get_current_datetime_in_timezone(timezone)
        context_dict = serialize_day_context(day_context, current_time)

        system_prompt = await render_for_user(
            query.usecase,
            "system",
            template_repo=self.template_ro_repo,
            user_id=self.user_id,
        )
        context_prompt = await render_for_user(
            query.usecase,
            "context",
            template_repo=self.template_ro_repo,
            user_id=self.user_id,
            context=day_context,
            current_time=current_time,
        )
        ask_prompt = await render_for_user(
            query.usecase,
            "ask",
            template_repo=self.template_ro_repo,
            user_id=self.user_id,
        )

        return PreviewTemplateResult(
            system_prompt=system_prompt,
            context_prompt=context_prompt,
            ask_prompt=ask_prompt,
            context_data=context_dict,
        )

    async def _get_today_context(self, timezone: str | None) -> LLMPromptContext:
        """Load today's LLM prompt context."""
        prompt_context_handler = GetLLMPromptContextHandler(
            self._ro_repos,
            self.user_id,
            GetDayContextHandler(self._ro_repos, self.user_id),
        )
        return await prompt_context_handler.handle(
            GetLLMPromptContextQuery(date=get_current_date(timezone))
        )
