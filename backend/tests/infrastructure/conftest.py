"""Fixtures for infrastructure tests."""

from uuid import uuid4

import pytest_asyncio

from lykke.domain.entities import UserEntity
from lykke.domain.value_objects.user import UserSetting
from lykke.infrastructure.repositories import (
    DayRepository,
    TaskRepository,
)
from lykke.infrastructure.unauthenticated import UnauthenticatedIdentityAccess


@pytest_asyncio.fixture
async def test_user():
    """Create a unique user for each test."""
    identity_access = UnauthenticatedIdentityAccess()
    uid = uuid4()
    user = UserEntity(
        id=uid,
        email=f"test-{uid}@example.com",
        phone_number=f"+1{uid.int % 10**10:010d}",
        hashed_password="test_hash",
        settings=UserSetting(),
    )
    await identity_access.create_user(user)
    return user


@pytest_asyncio.fixture
async def day_repo(test_user):
    """DayRepository scoped to test_user."""
    return DayRepository(user=test_user)


@pytest_asyncio.fixture
async def task_repo(test_user):
    """TaskRepository scoped to test_user."""
    return TaskRepository(user=test_user)
