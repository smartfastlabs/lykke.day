"""Query for building a synthetic LLM run snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from lykke.application.gateways.llm_protocol import LLMTool
from lykke.application.llm.prompt_rendering import (
    render_ask_prompt,
    render_context_prompt,
    render_system_prompt,
)
from lykke.application.llm.tools_prompt import render_tools_prompt
from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.queries.get_llm_prompt_context import (
    GetLLMPromptContextHandler,
    GetLLMPromptContextQuery,
)
from lykke.application.unit_of_work import ReadOnlyRepositories
from lykke.core.utils.dates import get_current_date, get_current_datetime_in_timezone
from lykke.core.utils.day_context_serialization import serialize_day_context
from lykke.core.utils.llm_snapshot import build_referenced_entities
from lykke.domain import value_objects


@dataclass(frozen=True)
class PreviewLLMSnapshotQuery(Query):
    """Query to build a synthetic LLM run snapshot."""

    usecase: str


class PreviewLLMSnapshotHandler(
    BaseQueryHandler[PreviewLLMSnapshotQuery, value_objects.LLMRunResultSnapshot | None]
):
    """Builds a synthetic LLM snapshot for a given usecase."""

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        user_id: UUID,
        get_llm_prompt_context_handler: GetLLMPromptContextHandler,
    ) -> None:
        super().__init__(ro_repos, user_id)
        self._get_llm_prompt_context_handler = get_llm_prompt_context_handler

    async def handle(
        self, query: PreviewLLMSnapshotQuery
    ) -> value_objects.LLMRunResultSnapshot | None:
        """Build a synthetic snapshot without running the LLM."""
        if query.usecase != "notification":
            return None

        user = await self.user_ro_repo.get(self.user_id)
        if not user.settings or not user.settings.llm_provider:
            return None

        current_time = get_current_datetime_in_timezone(user.settings.timezone)
        current_date = get_current_date(user.settings.timezone)
        prompt_context = await self._get_llm_prompt_context_handler.handle(
            GetLLMPromptContextQuery(date=current_date)
        )

        tools = self._build_notification_tools()
        tools_prompt = render_tools_prompt(tools)
        extra_template_vars = {"tools_prompt": tools_prompt}

        system_prompt = await render_system_prompt(
            usecase=query.usecase,
            user=user,
            usecase_config_ro_repo=self.usecase_config_ro_repo,
        )
        context_prompt = render_context_prompt(
            usecase=query.usecase,
            prompt_context=prompt_context,
            current_time=current_time,
            extra_template_vars=extra_template_vars,
        )
        ask_prompt = render_ask_prompt(
            usecase=query.usecase, extra_template_vars=extra_template_vars
        )

        return value_objects.LLMRunResultSnapshot(
            tool_calls=[
                value_objects.LLMToolCallResultSnapshot(
                    tool_name=tool.name or "tool",
                    arguments=self._default_tool_call_arguments(tool.name or "tool"),
                    result=None,
                )
                for tool in tools
            ],
            prompt_context=serialize_day_context(
                prompt_context, current_time=current_time
            ),
            current_time=current_time,
            llm_provider=user.settings.llm_provider,
            system_prompt=system_prompt,
            context_prompt=context_prompt,
            ask_prompt=ask_prompt,
            tools_prompt=tools_prompt,
            referenced_entities=build_referenced_entities(prompt_context),
        )

    @staticmethod
    def _build_notification_tools() -> list[LLMTool]:
        async def decide_notification(
            should_notify: bool,
            message: str | None = None,
            priority: str | None = None,
            reason: str | None = None,
        ) -> None:
            """Decide whether to send a smart notification."""
            _ = (should_notify, message, priority, reason)
            return None

        return [
            LLMTool(
                name="decide_notification",
                callback=decide_notification,
                description="Decide whether to send a smart notification.",
            )
        ]

    @staticmethod
    def _default_tool_call_arguments(tool_name: str) -> dict[str, object | None]:
        if tool_name == "decide_notification":
            return {
                "should_notify": None,
                "message": None,
                "priority": None,
                "reason": None,
            }
        return {}
