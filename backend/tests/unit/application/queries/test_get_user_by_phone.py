"""Unit tests for GetUserByPhoneHandler."""

from uuid import uuid4

import pytest

from lykke.application.queries.user import GetUserByPhoneHandler, GetUserByPhoneQuery
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from tests.unit.fakes import _FakeReadOnlyRepos


class _FakeUserRepo:
    def __init__(self, user: UserEntity | None = None) -> None:
        self._user = user

    async def search_one_or_none(
        self, query: value_objects.UserQuery
    ) -> UserEntity | None:
        if self._user and self._user.phone_number == query.phone_number:
            return self._user
        return None


@pytest.mark.asyncio
async def test_get_user_by_phone_returns_user_when_found():
    user = UserEntity(
        email="test@example.com",
        hashed_password="hash",
        phone_number="+15551234567",
    )
    ro_repos = _FakeReadOnlyRepos(user_repo=_FakeUserRepo(user))
    handler = GetUserByPhoneHandler(ro_repos=ro_repos, user_id=uuid4())

    result = await handler.handle(
        GetUserByPhoneQuery(phone_number="+15551234567")
    )

    assert result == user


@pytest.mark.asyncio
async def test_get_user_by_phone_returns_none_when_missing():
    user = UserEntity(
        email="test@example.com",
        hashed_password="hash",
        phone_number="+15551234567",
    )
    ro_repos = _FakeReadOnlyRepos(user_repo=_FakeUserRepo(user))
    handler = GetUserByPhoneHandler(ro_repos=ro_repos, user_id=uuid4())

    result = await handler.handle(
        GetUserByPhoneQuery(phone_number="+15550000000")
    )

    assert result is None
