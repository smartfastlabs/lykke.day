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
from tests.unit.fakes import _FakeReadOnlyRepos, _FakeUoW, _FakeUoWFactory, _FakeUserReadOnlyRepo


@pytest.mark.asyncio
async def test_update_user_updates_fields_and_settings():
    user = UserEntity(
        email="test@example.com",
        hashed_password="hash",
        settings=UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = _FakeUserReadOnlyRepo(user)
    ro_repos = _FakeReadOnlyRepos(user_repo=user_repo)
    uow = _FakeUoW(user_repo=user_repo)
    uow_factory = _FakeUoWFactory(uow)
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
    user_repo = _FakeUserReadOnlyRepo(user)
    ro_repos = _FakeReadOnlyRepos(user_repo=user_repo)
    uow = _FakeUoW(user_repo=user_repo)
    uow_factory = _FakeUoWFactory(uow)
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
