"""Fixtures for infrastructure tests."""

import pytest
import pytest_asyncio

from uuid import UUID, uuid4

from planned.domain.entities import User
from planned.domain.value_objects.user import UserSetting
from planned.infrastructure.repositories import DayRepository, TaskRepository, UserRepository


@pytest_asyncio.fixture
async def test_user():
    """Create a unique user for each test."""
    user_repo = UserRepository()
    user = User(
        id=str(uuid4()),
        email=f"test-{uuid4()}@example.com",
        password_hash="test_hash",
        settings=UserSetting(),
    )
    return await user_repo.put(user)


@pytest_asyncio.fixture
async def day_repo(test_user):
    """DayRepository scoped to test_user."""
    return DayRepository(user_uuid=UUID(test_user.id))


@pytest_asyncio.fixture
async def task_repo(test_user):
    """TaskRepository scoped to test_user."""
    return TaskRepository(user_uuid=UUID(test_user.id))

