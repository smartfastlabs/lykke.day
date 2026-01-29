"""LLM handler mixin for commands and queries."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from loguru import logger

from lykke.application.gateways.llm_gateway_factory_protocol import (
    LLMGatewayFactoryProtocol,
)
from lykke.application.gateways.llm_protocol import LLMTool, LLMToolCallResult
from lykke.application.llm.prompt_rendering import (
    render_ask_prompt,
    render_context_prompt,
    render_system_prompt,
)
from lykke.application.llm.tools_prompt import render_tools_prompt
from lykke.core.exceptions import DomainError
from lykke.core.utils.dates import get_current_date, get_current_datetime_in_timezone

if TYPE_CHECKING:
    from datetime import date as datetime_date
    from uuid import UUID

    from lykke.application.repositories import (
        UseCaseConfigRepositoryReadOnlyProtocol,
        UserRepositoryReadOnlyProtocol,
    )
    from lykke.domain import value_objects


@dataclass(frozen=True)
class UseCasePromptInput:
    """Prompt input for an LLM handler."""

    prompt_context: value_objects.LLMPromptContext
    extra_template_vars: dict[str, Any] | None = None


@dataclass(frozen=True)
class LLMRunResult:
    """Result returned by the LLM handler runner."""

    tool_results: list[LLMToolCallResult]
    prompt_context: value_objects.LLMPromptContext
    current_time: datetime
    llm_provider: value_objects.LLMProvider
    system_prompt: str
    context_prompt: str
    ask_prompt: str
    tools_prompt: str


@dataclass(frozen=True)
class LLMRunSnapshotContext:
    """Context needed to build an LLM run snapshot."""

    prompt_context: value_objects.LLMPromptContext
    current_time: datetime
    llm_provider: value_objects.LLMProvider
    system_prompt: str
    context_prompt: str
    ask_prompt: str
    tools_prompt: str


class LLMHandlerMixin(ABC):
    """Mixin for handlers that run LLM tool calls."""

    name: str
    template_usecase: str
    user_id: UUID
    user_ro_repo: UserRepositoryReadOnlyProtocol
    usecase_config_ro_repo: UseCaseConfigRepositoryReadOnlyProtocol
    _llm_gateway_factory: LLMGatewayFactoryProtocol
    _llm_snapshot_context: LLMRunSnapshotContext | None = None

    @abstractmethod
    async def build_prompt_input(self, date: datetime_date) -> UseCasePromptInput:
        """Build the prompt inputs for this handler."""

    @abstractmethod
    def build_tools(
        self,
        *,
        current_time: datetime,
        prompt_context: value_objects.LLMPromptContext,
        llm_provider: value_objects.LLMProvider,
    ) -> list[LLMTool]:
        """Build tool definitions for this handler."""

    async def run_llm(self) -> LLMRunResult | None:
        """Run the LLM flow for this handler."""
        try:
            user = await self.user_ro_repo.get(self.user_id)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error(f"Failed to load user {self.user_id}: {exc}")
            return None

        if not user.settings or not user.settings.llm_provider:
            logger.debug(
                f"User {self.user_id} has no LLM provider configured, skipping"
            )
            return None

        llm_provider = user.settings.llm_provider
        current_time = get_current_datetime_in_timezone(user.settings.timezone)
        current_date = get_current_date(user.settings.timezone)

        try:
            prompt_input = await self.build_prompt_input(current_date)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error(
                f"Failed to load LLM prompt context for user {self.user_id}: {exc}"
            )
            return None

        tools = self.build_tools(
            current_time=current_time,
            prompt_context=prompt_input.prompt_context,
            llm_provider=llm_provider,
        )
        if not tools:
            logger.error(f"Handler '{self.template_usecase}' returned no tools to call")
            return None

        tools_prompt = render_tools_prompt(tools)
        extra_template_vars = dict(prompt_input.extra_template_vars or {})
        extra_template_vars["tools_prompt"] = tools_prompt

        system_prompt = await render_system_prompt(
            usecase=self.template_usecase,
            user=user,
            usecase_config_ro_repo=self.usecase_config_ro_repo,
        )
        context_prompt = render_context_prompt(
            usecase=self.template_usecase,
            prompt_context=prompt_input.prompt_context,
            current_time=current_time,
            extra_template_vars=extra_template_vars,
        )
        ask_prompt = render_ask_prompt(
            usecase=self.template_usecase,
            extra_template_vars=extra_template_vars,
        )

        try:
            llm_gateway = self._llm_gateway_factory.create_gateway(llm_provider)
        except DomainError as exc:
            logger.error(
                f"Failed to create LLM gateway for provider {llm_provider}: {exc}"
            )
            return None

        tool_names = [tool.name for tool in tools]
        logger.info(
            f"Running LLM handler {self.template_usecase} with tools {tool_names}"
        )
        self._llm_snapshot_context = LLMRunSnapshotContext(
            prompt_context=prompt_input.prompt_context,
            current_time=current_time,
            llm_provider=llm_provider,
            system_prompt=system_prompt,
            context_prompt=context_prompt,
            ask_prompt=ask_prompt,
            tools_prompt=tools_prompt,
        )

        tool_result = await llm_gateway.run_usecase(
            system_prompt,
            context_prompt,
            ask_prompt,
            tools,
            metadata={
                "user_id": str(self.user_id),
                "handler": self.name,
                "usecase": self.template_usecase,
                "llm_provider": llm_provider.value,
            },
        )
        if tool_result is None:
            logger.debug(
                f"LLM returned no tool call for handler {self.template_usecase}"
            )
            return None

        return LLMRunResult(
            tool_results=tool_result.tool_results,
            prompt_context=prompt_input.prompt_context,
            current_time=current_time,
            llm_provider=llm_provider,
            system_prompt=system_prompt,
            context_prompt=context_prompt,
            ask_prompt=ask_prompt,
            tools_prompt=tools_prompt,
        )
