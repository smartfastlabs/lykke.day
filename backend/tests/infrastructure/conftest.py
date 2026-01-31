"""Fixtures for infrastructure tests."""

from uuid import uuid4

import pytest_asyncio

from lykke.domain.entities import UserEntity
from lykke.domain.value_objects.user import UserSetting
from lykke.infrastructure.repositories import (
    DayRepository,
    TaskRepository,
    UserRepository,
)


@pytest_asyncio.fixture
async def test_user():
    """Create a unique user for each test."""
    user_repo = UserRepository()
    uid = uuid4()
    user = UserEntity(
        id=uid,
        email=f"test-{uid}@example.com",
        phone_number=f"+1555{uid.hex[:7]}",
        hashed_password="test_hash",
        settings=UserSetting(),
    )
    return await user_repo.put(user)


@pytest_asyncio.fixture
async def day_repo(test_user):
    """DayRepository scoped to test_user."""
    return DayRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def task_repo(test_user):
    """TaskRepository scoped to test_user."""
    return TaskRepository(user_id=test_user.id)
