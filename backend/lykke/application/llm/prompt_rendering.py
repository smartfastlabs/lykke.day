"""Helpers for rendering LLM prompts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from lykke.application.repositories import UseCaseConfigRepositoryReadOnlyProtocol
from lykke.core.utils.day_context_serialization import serialize_day_context
from lykke.core.utils.templates import render_for_user
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity


async def fetch_user_amendments(
    usecase: str,
    usecase_config_ro_repo: UseCaseConfigRepositoryReadOnlyProtocol,
) -> list[str]:
    """Fetch user amendments for the given usecase."""
    configs = await usecase_config_ro_repo.search(
        value_objects.UseCaseConfigQuery(usecase=usecase)
    )
    if not configs:
        return []

    config = configs[0].config
    user_amendments = config.get("user_amendments", [])
    if isinstance(user_amendments, list):
        return user_amendments
    return []


async def render_system_prompt(
    *,
    usecase: str,
    user: UserEntity,
    usecase_config_ro_repo: UseCaseConfigRepositoryReadOnlyProtocol,
) -> str:
    """Render the system prompt for a usecase."""
    user_amendments = await fetch_user_amendments(usecase, usecase_config_ro_repo)
    base_personality_slug = None
    llm_personality_amendments: list[str] | None = None
    user_timezone = None
    if user.settings:
        base_personality_slug = user.settings.base_personality_slug
        llm_personality_amendments = user.settings.llm_personality_amendments
        user_timezone = user.settings.timezone
    user_name = user.email
    return render_for_user(
        usecase,
        "system",
        user_amendments=user_amendments,
        base_personality_slug=base_personality_slug,
        llm_personality_amendments=llm_personality_amendments,
        user=user,
        user_name=user_name,
        user_timezone=user_timezone,
    )


def render_context_prompt(
    *,
    usecase: str,
    prompt_context: value_objects.LLMPromptContext,
    current_time: datetime,
    extra_template_vars: dict[str, Any],
) -> str:
    """Render the context prompt for a usecase."""
    context_json = serialize_day_context(prompt_context, current_time=current_time)
    return render_for_user(
        usecase,
        "context",
        context=prompt_context,
        context_json=context_json,
        current_time=current_time,
        **extra_template_vars,
    )


def render_ask_prompt(*, usecase: str, extra_template_vars: dict[str, Any]) -> str:
    """Render the ask prompt for a usecase."""
    return render_for_user(usecase, "ask", **extra_template_vars)
