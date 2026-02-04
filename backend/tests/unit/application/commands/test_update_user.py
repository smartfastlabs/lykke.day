"""Unit tests for UpdateUserHandler."""

import pytest

from lykke.application.commands.user import UpdateUserCommand, UpdateUserHandler
from lykke.domain.entities import UserEntity
from lykke.domain.value_objects import (
    UserSetting,
    UserSettingUpdate,
    UserStatus,
    UserUpdateObject,
)
from tests.support.dobles import (
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
)


class _RepositoryFactory:
    def __init__(self, ro_repos: object) -> None:
        self._ro_repos = ro_repos

    def create(self, user: object) -> object:
        _ = user
        return self._ro_repos


class _FakeCurrentUserAccess:
    last_updated: UserEntity | None = None

    async def update_user(self, updated: UserEntity) -> UserEntity:
        self.last_updated = updated
        return updated


@pytest.mark.asyncio
async def test_update_user_updates_fields_and_settings():
    user = UserEntity(
        email="test@example.com",
        hashed_password="hash",
        settings=UserSetting(template_defaults=["default"] * 7),
    )
    ro_repos = create_read_only_repos_double()
    uow = create_uow_double()
    uow_factory = create_uow_factory_double(uow)
    handler = UpdateUserHandler(
        user=user,
        uow_factory=uow_factory,
        repository_factory=_RepositoryFactory(ro_repos),
    )
    fake_access = _FakeCurrentUserAccess()
    handler.current_user_access = fake_access  # type: ignore[assignment]

    update_data = UserUpdateObject(
        phone_number="(978) 844-4177",
        status=UserStatus.NEW_LEAD,
        settings_update=UserSettingUpdate.from_dict(
            {"template_defaults": ["a", "b", "c", "d", "e", "f", "g"]}
        ),
    )

    updated = await handler.handle(UpdateUserCommand(update_data=update_data))

    assert updated.phone_number == "+19788444177"
    assert updated.status == UserStatus.NEW_LEAD
    assert updated.settings.template_defaults == ["a", "b", "c", "d", "e", "f", "g"]
    assert fake_access.last_updated == updated


@pytest.mark.asyncio
async def test_update_user_skips_none_fields():
    user = UserEntity(
        email="test@example.com",
        hashed_password="hash",
        settings=UserSetting(template_defaults=["default"] * 7),
    )
    ro_repos = create_read_only_repos_double()
    uow = create_uow_double()
    uow_factory = create_uow_factory_double(uow)
    handler = UpdateUserHandler(
        user=user,
        uow_factory=uow_factory,
        repository_factory=_RepositoryFactory(ro_repos),
    )
    fake_access = _FakeCurrentUserAccess()
    handler.current_user_access = fake_access  # type: ignore[assignment]

    update_data = UserUpdateObject(
        phone_number=None,
        status=None,
        settings_update=None,
    )

    updated = await handler.handle(UpdateUserCommand(update_data=update_data))

    assert updated.phone_number == user.phone_number
    assert updated.status == user.status
    assert updated.settings.template_defaults == user.settings.template_defaults
    assert fake_access.last_updated == updated
