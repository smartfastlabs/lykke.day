"""Unit tests for GenerateUseCasePromptHandler."""

from uuid import uuid4

import pytest

from lykke.application.queries.generate_usecase_prompt import (
    GenerateUseCasePromptHandler,
    GenerateUseCasePromptQuery,
)
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity


class _FakeUseCaseConfigReadOnlyRepo:
    async def search(self, _query):
        return []


class _FakeUserReadOnlyRepo:
    def __init__(self, user: UserEntity) -> None:
        self._user = user

    async def get(self, _user_id):
        return self._user


class _FakeReadOnlyRepos:
    """Minimal read-only repos container for BaseQueryHandler."""

    def __init__(
        self,
        usecase_config_repo: _FakeUseCaseConfigReadOnlyRepo,
        user_repo: _FakeUserReadOnlyRepo,
    ) -> None:
        fake = object()
        self.audit_log_ro_repo = fake
        self.auth_token_ro_repo = fake
        self.bot_personality_ro_repo = fake
        self.calendar_entry_ro_repo = fake
        self.calendar_entry_series_ro_repo = fake
        self.calendar_ro_repo = fake
        self.conversation_ro_repo = fake
        self.day_ro_repo = fake
        self.day_template_ro_repo = fake
        self.factoid_ro_repo = fake
        self.message_ro_repo = fake
        self.push_notification_ro_repo = fake
        self.push_subscription_ro_repo = fake
        self.routine_ro_repo = fake
        self.task_definition_ro_repo = fake
        self.task_ro_repo = fake
        self.time_block_definition_ro_repo = fake
        self.usecase_config_ro_repo = usecase_config_repo
        self.user_ro_repo = user_repo


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
        _FakeUseCaseConfigReadOnlyRepo(),
        _FakeUserReadOnlyRepo(user),
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
