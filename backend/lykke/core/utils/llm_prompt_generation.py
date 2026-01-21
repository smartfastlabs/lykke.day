"""Utility for generating LLM prompts for use cases."""
from datetime import datetime
from uuid import UUID

from lykke.application.llm_usecases.base import BaseUseCase
from lykke.application.repositories import TemplateRepositoryReadOnlyProtocol
from lykke.core.utils.templates import render_for_user
from lykke.domain import value_objects


async def generate_usecase_prompts(
    usecase: BaseUseCase,
    context: value_objects.LLMPromptContext,
    current_time: datetime,
    template_repo: TemplateRepositoryReadOnlyProtocol,
    user_id: UUID,
) -> tuple[str, str, str]:
    """Generate system, context, and ask prompts for an LLM use case.

    Args:
        usecase: The LLM use case definition
        context: The user's current LLM prompt context
        current_time: The current datetime
        template_repo: Template repository for user overrides
        user_id: The user ID for template scoping

    Returns:
        A tuple of (system_prompt, context_prompt, ask_prompt)
    """
    # Render prompt parts from templates
    system_prompt = await render_for_user(
        usecase.template_usecase,
        "system",
        template_repo=template_repo,
        user_id=user_id,
    )
    context_prompt = await render_for_user(
        usecase.template_usecase,
        "context",
        template_repo=template_repo,
        user_id=user_id,
        context=context,
        current_time=current_time,
    )
    ask_prompt = await render_for_user(
        usecase.template_usecase,
        "ask",
        template_repo=template_repo,
        user_id=user_id,
    )

    return system_prompt, context_prompt, ask_prompt
