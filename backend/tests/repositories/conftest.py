"""Fixtures for repository tests."""

import datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio

from planned import settings
from planned.domain import entities as objects
from planned.domain.value_objects.user import UserSetting
from planned.infrastructure.repositories import UserRepository


@pytest_asyncio.fixture
async def test_user():
    """Create a unique user for each test."""
    user_repo = UserRepository()
    user = objects.User(
        id=str(uuid4()),
        email=f"test-{uuid4()}@example.com",
        password_hash="test_hash",
        settings=UserSetting(),
    )
    return await user_repo.put(user)


@pytest_asyncio.fixture
async def test_event(test_user, test_date):
    """Create a test event."""
    starts_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=2),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    )
    return objects.Event(
        user_uuid=UUID(test_user.id),
        name="Test Event",
        frequency="ONCE",
        calendar_id="test-calendar",
        platform_id="test-id",
        platform="testing",
        status="status",
        starts_at=starts_at,
        date=test_date,
    )


@pytest_asyncio.fixture
async def clear_repos():
    """Clear all repositories - placeholder for now."""
    # This is a no-op for now, but can be implemented if needed
    yield
