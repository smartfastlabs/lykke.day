"""Unit tests for UpdateUserHandler."""

# pylint: disable=import-error
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from lykke.application.commands.user import UpdateUserCommand, UpdateUserHandler
from lykke.domain.entities import UserEntity
from lykke.domain.value_objects import UserSetting, UserStatus, UserUpdateObject


class _FakeUserReadOnlyRepo:
    def __init__(self, user: UserEntity) -> None:
        self._user = user

    async def get(self, _user_id):
        return self._user


class _FakeReadOnlyRepos:
    """Lightweight container matching ReadOnlyRepositories protocol."""

    def __init__(self, user: UserEntity) -> None:
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
        self.push_subscription_ro_repo = fake
        self.routine_ro_repo = fake
        self.task_definition_ro_repo = fake
        self.task_ro_repo = fake
        self.time_block_definition_ro_repo = fake
        self.user_ro_repo = _FakeUserReadOnlyRepo(user)


class _FakeUoW:
    """Minimal UnitOfWork that just collects added entities."""

    def __init__(self, user_ro_repo) -> None:
        self.added = []
        self.user_ro_repo = user_ro_repo

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    def add(self, entity):
        self.added.append(entity)


class _FakeUoWFactory:
    def __init__(self, user_ro_repo) -> None:
        self.uow = _FakeUoW(user_ro_repo)

    def create(self, _user_id):
        return self.uow


@pytest.mark.asyncio
async def test_update_user_updates_fields_and_settings():
    user = UserEntity(
        email="test@example.com",
        hashed_password="hash",
        settings=UserSetting(template_defaults=["default"] * 7),
    )
    ro_repos = _FakeReadOnlyRepos(user)
    uow_factory = _FakeUoWFactory(ro_repos.user_ro_repo)
    handler = UpdateUserHandler(ro_repos, uow_factory, user.id)

    update_data = UserUpdateObject(
        phone_number="123",
        status=UserStatus.NEW_LEAD,
        settings=UserSetting(template_defaults=["a", "b", "c", "d", "e", "f", "g"]),
    )

    updated = await handler.handle(UpdateUserCommand(update_data=update_data))

    assert updated.phone_number == "123"
    assert updated.status == UserStatus.NEW_LEAD
    assert updated.settings.template_defaults == ["a", "b", "c", "d", "e", "f", "g"]
    assert uow_factory.uow.added == [updated]


@pytest.mark.asyncio
async def test_update_user_skips_none_fields():
    user = UserEntity(
        email="test@example.com",
        hashed_password="hash",
        settings=UserSetting(template_defaults=["default"] * 7),
    )
    ro_repos = _FakeReadOnlyRepos(user)
    uow_factory = _FakeUoWFactory(ro_repos.user_ro_repo)
    handler = UpdateUserHandler(ro_repos, uow_factory, user.id)

    update_data = UserUpdateObject(
        phone_number=None,
        status=None,
        settings=None,
    )

    updated = await handler.handle(UpdateUserCommand(update_data=update_data))

    assert updated.phone_number == user.phone_number
    assert updated.status == user.status
    assert updated.settings.template_defaults == user.settings.template_defaults
    assert uow_factory.uow.added == [updated]
