"""Fixtures for integration tests - uses real database with per-test user isolation."""

from datetime import time
from uuid import uuid4

import pytest
import pytest_asyncio

from planned.domain.entities import UserEntity
from planned.domain.entities.day_template import DayTemplateEntity
from planned.domain.value_objects.alarm import Alarm, AlarmType
from planned.domain.value_objects.user import UserSetting
from planned.infrastructure.repositories import (
    AuthTokenRepository,
    CalendarEntryRepository,
    CalendarRepository,
    DayRepository,
    DayTemplateRepository,
    PushSubscriptionRepository,
    RoutineRepository,
    TaskDefinitionRepository,
    TaskRepository,
    UserRepository,
)


@pytest_asyncio.fixture
async def create_test_user():
    """Factory to create unique test users."""

    async def _create_user(email: str | None = None, **kwargs) -> UserEntity:
        """Create a test user with unique email."""
        if email is None:
            email = f"test-{uuid4()}@example.com"

        user = UserEntity(
            email=email,
            hashed_password="test_hash",
            settings=kwargs.pop("settings", UserSetting()),
            **kwargs,
        )
        user_repo = UserRepository()
        return await user_repo.put(user)

    return _create_user


@pytest_asyncio.fixture
async def test_user(create_test_user):
    """Create a unique user for each test."""
    return await create_test_user(
        settings=UserSetting(
            template_defaults=[
                "default",
                "default",
                "default",
                "default",
                "default",
                "weekend",
                "weekend",
            ],
        ),
    )


async def _setup_day_templates_for_user(user: UserEntity) -> None:
    """Helper function to create default day templates for a user."""
    repo = DayTemplateRepository(user_id=user.id)

    # Create default template (UUID will be auto-generated from slug + user_id)
    default_template = DayTemplateEntity(
        user_id=user.id,
        slug="default",
        alarm=Alarm(
            name="Default Alarm",
            time=time(7, 15),
            type=AlarmType.FIRM,
        ),
    )
    await repo.put(default_template)

    # Create weekend template (UUID will be auto-generated from slug + user_id)
    weekend_template = DayTemplateEntity(
        user_id=user.id,
        slug="weekend",
        alarm=Alarm(
            name="Weekend Alarm",
            time=time(7, 15),
            type=AlarmType.GENTLE,
        ),
    )
    await repo.put(weekend_template)


@pytest.fixture
def setup_day_templates(test_user):
    """Create default and weekend day templates for tests."""
    return _setup_day_templates_for_user(test_user)


# Repository fixtures - all scoped to test_user
@pytest_asyncio.fixture
async def user_repo():
    """UserRepository - not user-scoped."""
    return UserRepository()


@pytest_asyncio.fixture
async def day_repo(test_user):
    """DayRepository scoped to test_user."""
    return DayRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def day_template_repo(test_user):
    """DayTemplateRepository scoped to test_user."""
    return DayTemplateRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def calendar_entry_repo(test_user):
    """CalendarEntryRepository scoped to test_user."""
    return CalendarEntryRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def task_repo(test_user):
    """TaskRepository scoped to test_user."""
    return TaskRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def calendar_repo(test_user):
    """CalendarRepository scoped to test_user."""
    return CalendarRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def auth_token_repo(test_user):
    """AuthTokenRepository (not user-scoped)."""
    return AuthTokenRepository()


@pytest_asyncio.fixture
async def push_subscription_repo(test_user):
    """PushSubscriptionRepository scoped to test_user."""
    return PushSubscriptionRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def routine_repo(test_user):
    """RoutineRepository scoped to test_user."""
    return RoutineRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def task_definition_repo(test_user):
    """TaskDefinitionRepository scoped to test_user."""
    return TaskDefinitionRepository(user_id=test_user.id)
