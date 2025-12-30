"""Fixtures for repository tests."""

import datetime
from datetime import UTC
from uuid import UUID, uuid4, uuid5, NAMESPACE_DNS
from zoneinfo import ZoneInfo

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
        uuid=uuid4(),
        email=f"test-{uuid4()}@example.com",
        hashed_password="test_hash",
        settings=UserSetting(),
    )
    return await user_repo.put(user)


@pytest_asyncio.fixture
async def test_event(test_user, test_date):
    """Create a test event."""
    # Create datetime in configured timezone, then convert to UTC
    starts_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=2),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    return objects.Event(
        user_id=test_user.id,
        name="Test Event",
        frequency="ONCE",
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
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
