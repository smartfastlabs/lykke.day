"""Unit tests for GetUserByPhoneHandler."""

from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.queries.user import GetUserByPhoneHandler, GetUserByPhoneQuery
from lykke.domain.entities import UserEntity
from tests.support.dobles import (
    create_read_only_repos_double,
    create_user_repo_double,
)


@pytest.mark.asyncio
async def test_get_user_by_phone_returns_user_when_found():
    user = UserEntity(
        email="test@example.com",
        hashed_password="hash",
        phone_number="+15551234567",
    )
    user_repo = create_user_repo_double()
    allow(user_repo).search_one_or_none.and_return(user)

    ro_repos = create_read_only_repos_double(user_repo=user_repo)
    handler = GetUserByPhoneHandler(ro_repos=ro_repos, user_id=uuid4())

    result = await handler.handle(
        GetUserByPhoneQuery(phone_number="+15551234567")
    )

    assert result == user


@pytest.mark.asyncio
async def test_get_user_by_phone_returns_none_when_missing():
    user_repo = create_user_repo_double()
    allow(user_repo).search_one_or_none.and_return(None)

    ro_repos = create_read_only_repos_double(user_repo=user_repo)
    handler = GetUserByPhoneHandler(ro_repos=ro_repos, user_id=uuid4())

    result = await handler.handle(
        GetUserByPhoneQuery(phone_number="+15550000000")
    )

    assert result is None
