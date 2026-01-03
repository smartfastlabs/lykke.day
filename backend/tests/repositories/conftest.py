"""Fixtures for repository tests."""

import datetime
from datetime import UTC
from uuid import NAMESPACE_DNS, UUID, uuid4, uuid5
from zoneinfo import ZoneInfo

import pytest_asyncio
from planned import settings
from planned.domain.entities import CalendarEntity, CalendarEntryEntity, UserEntity
from planned.domain.value_objects.task import TaskFrequency
from planned.domain.value_objects.user import UserSetting
from planned.infrastructure.repositories import UserRepository


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
async def test_calendar_entry(test_user, test_date):
    """Create a test calendar entry."""
    # Create datetime in configured timezone, then convert to UTC
    starts_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=2),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    return CalendarEntryEntity(
        user_id=test_user.id,
        name="Test Calendar Entry",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-id",
        platform="testing",
        status="status",
        starts_at=starts_at,
    )


@pytest_asyncio.fixture
async def clear_repos():
    """Clear all repositories - placeholder for now."""
    # This is a no-op for now, but can be implemented if needed
    yield
