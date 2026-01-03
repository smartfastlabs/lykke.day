"""Fixtures for infrastructure tests."""

import pytest_asyncio

from uuid import uuid4

from planned.domain.entities import UserEntity
from planned.domain.value_objects.user import UserSetting
from planned.infrastructure.repositories import DayRepository, TaskRepository, UserRepository


@pytest_asyncio.fixture
async def test_user():
    """Create a unique user for each test."""
    user_repo = UserRepository()
    user = UserEntity(
        id=uuid4(),
        email=f"test-{uuid4()}@example.com",
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

