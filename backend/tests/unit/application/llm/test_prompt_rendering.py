"""Unit tests for prompt rendering helpers."""

from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.llm import render_system_prompt
from lykke.application.repositories import UseCaseConfigRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from tests.support.dobles import create_repo_double


@pytest.mark.asyncio
async def test_render_system_prompt_uses_base_personality_slug() -> None:
    """Ensure system prompt includes base personality template."""
    user_id = uuid4()
    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(
            template_defaults=["default"] * 7,
            base_personality_slug="direct",
        ),
    )

    usecase_config_repo = create_repo_double(UseCaseConfigRepositoryReadOnlyProtocol)
    allow(usecase_config_repo).search.and_return([])

    result = await render_system_prompt(
        usecase="notification",
        user=user,
        usecase_config_ro_repo=usecase_config_repo,
    )

    assert "no-nonsense assistant" in result
