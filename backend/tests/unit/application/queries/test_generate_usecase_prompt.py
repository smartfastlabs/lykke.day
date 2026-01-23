"""Unit tests for GenerateUseCasePromptHandler."""

from uuid import uuid4

import pytest

from lykke.application.queries.generate_usecase_prompt import (
    GenerateUseCasePromptHandler,
    GenerateUseCasePromptQuery,
)
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from tests.unit.fakes import (
    _FakeReadOnlyRepos,
    _FakeUseCaseConfigReadOnlyRepo,
    _FakeUserReadOnlyRepo,
)


@pytest.mark.asyncio
async def test_generate_usecase_prompt_uses_base_personality_slug() -> None:
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

    ro_repos = _FakeReadOnlyRepos(
        usecase_config_repo=_FakeUseCaseConfigReadOnlyRepo(),
        user_repo=_FakeUserReadOnlyRepo(user),
    )
    handler = GenerateUseCasePromptHandler(ro_repos, user_id)

    result = await handler.handle(
        GenerateUseCasePromptQuery(
            usecase="notification",
            include_context=False,
            include_ask=False,
        )
    )

    assert "no-nonsense assistant" in result.system_prompt
