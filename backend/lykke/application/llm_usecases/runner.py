"""Runner for LLM use cases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from loguru import logger

from lykke.application.gateways.llm_gateway_factory import LLMGatewayFactory
from lykke.application.gateways.llm_protocol import LLMToolCallResult
from lykke.application.queries import (
    GenerateUseCasePromptHandler,
    GenerateUseCasePromptQuery,
)
from lykke.application.repositories import UserRepositoryReadOnlyProtocol
from lykke.core.exceptions import DomainError
from lykke.core.utils.dates import get_current_date, get_current_datetime_in_timezone

from .base import BaseUseCase

if TYPE_CHECKING:
    from lykke.domain import value_objects


@dataclass(frozen=True)
class LLMRunResult:
    """Result returned by the LLM use case runner."""

    tool_name: str
    result: object | None
    prompt_context: value_objects.LLMPromptContext
    current_time: datetime
    llm_provider: value_objects.LLMProvider
    system_prompt: str
    context_prompt: str
    ask_prompt: str


class LLMUseCaseRunner:
    """Shared runner for LLM use cases."""

    user_ro_repo: UserRepositoryReadOnlyProtocol

    def __init__(
        self,
        *,
        user_id: UUID,
        user_ro_repo: UserRepositoryReadOnlyProtocol,
        generate_usecase_prompt_handler: GenerateUseCasePromptHandler,
    ) -> None:
        self._user_id = user_id
        self._user_ro_repo = user_ro_repo
        self._generate_usecase_prompt_handler = generate_usecase_prompt_handler

    async def run(self, *, usecase: BaseUseCase) -> LLMRunResult | None:
        """Run an LLM use case and return the tool result."""
        try:
            user = await self._user_ro_repo.get(self._user_id)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error(f"Failed to load user {self._user_id}: {exc}")
            return None

        if not user.settings or not user.settings.llm_provider:
            logger.debug(
                f"User {self._user_id} has no LLM provider configured, skipping"
            )
            return None

        llm_provider = user.settings.llm_provider
        current_time = get_current_datetime_in_timezone(user.settings.timezone)
        current_date = get_current_date(user.settings.timezone)

        try:
            prompt_input = await usecase.build_prompt_input(current_date)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error(
                f"Failed to load LLM prompt context for user {self._user_id}: {exc}"
            )
            return None

        prompt_result = await self._generate_usecase_prompt_handler.handle(
            GenerateUseCasePromptQuery(
                usecase=usecase.template_usecase,
                prompt_context=prompt_input.prompt_context,
                current_time=current_time,
                include_context=True,
                include_ask=True,
                extra_template_vars=prompt_input.extra_template_vars,
            )
        )
        if prompt_result.context_prompt is None or prompt_result.ask_prompt is None:
            raise RuntimeError("Prompt generation did not include all prompt parts")

        try:
            llm_gateway = LLMGatewayFactory.create_gateway(llm_provider)
        except DomainError as exc:
            logger.error(
                f"Failed to create LLM gateway for provider {llm_provider}: {exc}"
            )
            return None

        tools = usecase.build_tools(
            current_time=current_time, prompt_context=prompt_input.prompt_context
        )
        if not tools:
            logger.error(
                f"Usecase '{usecase.template_usecase}' returned no tools to call"
            )
            return None

        tool_names = [tool.name for tool in tools]
        logger.info(
            f"Running LLM usecase {usecase.template_usecase} with tools {tool_names}"
        )
        tool_result: LLMToolCallResult | None = await llm_gateway.run_usecase(
            prompt_result.system_prompt,
            prompt_result.context_prompt,
            prompt_result.ask_prompt,
            tools,
        )
        if tool_result is None:
            logger.debug(
                f"LLM returned no tool call for usecase {usecase.template_usecase}"
            )
            return None

        return LLMRunResult(
            tool_name=tool_result.tool_name,
            result=tool_result.result,
            prompt_context=prompt_input.prompt_context,
            current_time=current_time,
            llm_provider=llm_provider,
            system_prompt=prompt_result.system_prompt,
            context_prompt=prompt_result.context_prompt,
            ask_prompt=prompt_result.ask_prompt,
        )
