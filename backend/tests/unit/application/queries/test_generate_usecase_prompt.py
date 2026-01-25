"""Unit tests for GenerateUseCasePromptHandler."""

from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.queries.generate_usecase_prompt import (
    GenerateUseCasePromptHandler,
    GenerateUseCasePromptQuery,
)
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from tests.support.dobles import (
    create_read_only_repos_double,
    create_repo_double,
    create_user_repo_double,
)
from lykke.application.repositories import UseCaseConfigRepositoryReadOnlyProtocol


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

    usecase_config_repo = create_repo_double(UseCaseConfigRepositoryReadOnlyProtocol)
    allow(usecase_config_repo).search.and_return([])

    user_repo = create_user_repo_double()
    allow(user_repo).get.with_args(user_id).and_return(user)

    ro_repos = create_read_only_repos_double(
        usecase_config_repo=usecase_config_repo,
        user_repo=user_repo,
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
