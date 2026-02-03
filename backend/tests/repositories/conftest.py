"""Fixtures for repository tests."""

import datetime
from datetime import UTC
from uuid import NAMESPACE_DNS, UUID, uuid4, uuid5
from zoneinfo import ZoneInfo

import pytest_asyncio

from lykke.domain.entities import (
    AuthTokenEntity,
    CalendarEntity,
    CalendarEntryEntity,
    UserEntity,
)
from lykke.domain.value_objects.task import TaskFrequency
from lykke.domain.value_objects.user import UserSetting
from lykke.infrastructure.repositories import (
    AuthTokenRepository,
    CalendarRepository,
    UserRepository,
)

USER_TIMEZONE = "America/Chicago"


@pytest_asyncio.fixture
async def test_user():
    """Create a unique user for each test."""
    user_repo = UserRepository()
    uid = uuid4()
    user = UserEntity(
        id=uid,
        email=f"test-{uid}@example.com",
        phone_number=f"+1{uid.int % 10**10:010d}",
        hashed_password="test_hash",
        settings=UserSetting(timezone=USER_TIMEZONE),
    )
    return await user_repo.put(user)


@pytest_asyncio.fixture
async def test_auth_token(test_user):
    """Create an auth token for the test user."""
    auth_token_repo = AuthTokenRepository(user=test_user)
    auth_token = AuthTokenEntity(
        user_id=test_user.id,
        platform="google",
        token="test_token",
    )
    return await auth_token_repo.put(auth_token)


@pytest_asyncio.fixture
async def test_calendar(test_user, test_auth_token):
    """Create a calendar for the test user."""
    calendar_repo = CalendarRepository(user=test_user)
    calendar = CalendarEntity(
        user_id=test_user.id,
        name="Test Calendar",
        auth_token_id=test_auth_token.id,
        platform="google",
        platform_id="test-calendar",
    )
    return await calendar_repo.put(calendar)


@pytest_asyncio.fixture
async def test_calendar_entry(test_user, test_date, test_calendar):
    """Create a test calendar entry."""
    # Create datetime in user timezone, then convert to UTC
    starts_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=2),
        tzinfo=ZoneInfo(USER_TIMEZONE),
    ).astimezone(UTC)
    return CalendarEntryEntity(
        user_id=test_user.id,
        name="Test Calendar Entry",
        frequency=TaskFrequency.ONCE,
        calendar_id=test_calendar.id,
        platform_id="test-id",
        platform="testing",
        status="status",
        starts_at=starts_at,
        user_timezone=USER_TIMEZONE,
    )


@pytest_asyncio.fixture
async def clear_repos():
    """Clear all repositories - placeholder for now."""
    # This is a no-op for now, but can be implemented if needed
    yield
