import datetime
import os
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio
from dobles import allow
from fastapi.testclient import TestClient
from freezegun import freeze_time

from planned import settings
from planned.app import app
from planned.application import services
from planned.domain import entities as objects
from planned.infrastructure.database import get_engine
from planned.infrastructure.utils.dates import get_current_date, get_current_datetime
from planned.presentation.middlewares import middlewares


@pytest.fixture(scope="session")
def test_database_url():
    """Get test database URL - should be PostgreSQL for tests."""
    # Use DATABASE_URL from environment if set, otherwise use settings
    # This allows the Makefile to set the test database URL
    database_url = (
        os.getenv("DATABASE_URL")
        or os.getenv("TEST_DATABASE_URL")
        or settings.DATABASE_URL
    )
    return database_url


@pytest_asyncio.fixture(autouse=True)
async def clear_database():
    """Clear database between tests."""
    from sqlalchemy import text

    # Truncate all tables for PostgreSQL
    engine = get_engine()
    async with engine.begin() as conn:
        # Get all table names
        result = await conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        )
        tables = [row[0] for row in result]

        # Truncate all tables
        if tables:
            await conn.execute(
                text(f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE")
            )

    yield


@pytest_asyncio.fixture
async def clear_repos(test_user):
    """Clear all data from the database, then recreate user and day templates."""
    from sqlalchemy import text

    from planned.infrastructure.repositories import UserRepository

    engine = get_engine()
    async with engine.begin() as conn:
        # Get all table names
        result = await conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        )
        tables = [row[0] for row in result]

        # Truncate all tables
        if tables:
            await conn.execute(
                text(f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE")
            )

    # Recreate user after clearing (since clear_repos clears everything)
    user_repo = UserRepository()
    recreated_user = await user_repo.put(test_user)

    # Recreate day templates after clearing (they're needed for many operations)
    await _setup_day_templates_for_user(recreated_user)


# Note: load_user_settings has been removed - services now use UserRepository
# Tests should provide User entities with UserSetting values as needed


@pytest_asyncio.fixture
async def test_user():
    """Create a test user for all tests."""
    from uuid import uuid4

    from planned.domain.entities import User
    from planned.domain.value_objects.user import UserSetting
    from planned.infrastructure.repositories import UserRepository

    user_repo = UserRepository()
    test_user = User(
        id=str(uuid4()),
        email="test@example.com",
        password_hash="test_hash",
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
    return await user_repo.put(test_user)


async def _setup_day_templates_for_user(user):
    """Helper function to create day templates for a user."""
    from datetime import time
    from uuid import UUID

    from planned.domain.entities import Alarm, DayTemplate
    from planned.domain.value_objects.alarm import AlarmType
    from planned.infrastructure.repositories import DayTemplateRepository

    repo = DayTemplateRepository(user_uuid=UUID(user.id))

    # Create default template
    default_template = DayTemplate(
        user_uuid=UUID(user.id),
        id="default",
        tasks=[],
        alarm=Alarm(
            name="Default Alarm",
            time=time(7, 15),
            type=AlarmType.FIRM,
        ),
    )
    await repo.put(default_template)

    # Create weekend template
    weekend_template = DayTemplate(
        user_uuid=UUID(user.id),
        id="weekend",
        tasks=[],
        alarm=Alarm(
            name="Weekend Alarm",
            time=time(7, 15),
            type=AlarmType.GENTLE,
        ),
    )
    await repo.put(weekend_template)


@pytest_asyncio.fixture(autouse=True)
async def setup_day_templates(test_user):
    """Create default and weekend day templates for tests."""
    await _setup_day_templates_for_user(test_user)
    yield


@pytest.fixture
def today():
    return get_current_date()


@pytest.fixture
def test_date():
    with freeze_time(
        "2025-11-27 00:00:00-6:00",
        real_asyncio=True,
    ):
        yield datetime.date(2025, 11, 27)


@pytest.fixture
def test_date_tomorrow(test_date):
    return test_date + datetime.timedelta(days=1)


@pytest.fixture
def test_client(clear_repos):
    # Make a request that sets up the session, then modify it
    with TestClient(app) as client:
        allow(middlewares.auth).mock_for_testing.and_return(True)
        yield client


@pytest.fixture
def test_deleted_event(test_date_tomorrow, test_user):
    from uuid import UUID
    starts_at = datetime.datetime.combine(
        test_date_tomorrow,
        datetime.time(hour=2),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    )
    return objects.Event(
        user_uuid=UUID(test_user.id),
        name="Test Event",
        calendar_id="test-calendar",
        platform_id="test-id",
        platform="testing",
        status="cancelled",
        starts_at=starts_at,
    )


@pytest.fixture
def test_event(test_date_tomorrow, test_user):
    from uuid import UUID
    starts_at = datetime.datetime.combine(
        test_date_tomorrow,
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
    )


@pytest.fixture
def test_event_today(test_date, test_user):
    from uuid import UUID
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
    )


@pytest.fixture
def test_calendar(test_auth_token, test_user):
    from uuid import UUID
    return objects.Calendar(
        user_uuid=UUID(test_user.id),
        name="Test Calendar",
        auth_token_id=test_auth_token.id,
        platform="google",
        platform_id="platform_id",
    )


@pytest.fixture
def test_auth_token(test_user):
    from uuid import UUID
    return objects.AuthToken(
        user_uuid=UUID(test_user.id),
        platform="testing",
        platform_id="test-auth-token",
        token="token",
    )


@pytest.fixture
def test_day(test_date, test_user):
    from uuid import UUID
    return objects.Day(
        user_uuid=UUID(test_user.id),
        date=test_date,
        status=objects.DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
    )


@pytest.fixture
def test_day_ctx(
    test_day,
    test_event_today,
    test_task_today,
):
    return objects.DayContext(
        day=test_day,
        tasks=[test_task_today],
        events=[test_event_today],
        messages=[],
    )


@pytest_asyncio.fixture
async def test_day_svc(test_day_ctx, test_user):
    from uuid import UUID

    from planned.infrastructure.repositories import (
        DayRepository,
        DayTemplateRepository,
        EventRepository,
        MessageRepository,
        TaskRepository,
    )

    user_uuid = UUID(test_user.id)
    day_repo = DayRepository(user_uuid=user_uuid)
    day_template_repo = DayTemplateRepository(user_uuid=user_uuid)
    event_repo = EventRepository(user_uuid=user_uuid)
    message_repo = MessageRepository(user_uuid=user_uuid)
    task_repo = TaskRepository(user_uuid=user_uuid)

    return services.DayService(
        ctx=test_day_ctx,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
    )


@pytest_asyncio.fixture
async def test_sheppard_svc(test_day_svc, test_user):
    from uuid import UUID

    from planned.application.services import CalendarService, PlanningService
    from planned.infrastructure.repositories import (
        AuthTokenRepository,
        CalendarRepository,
        DayRepository,
        DayTemplateRepository,
        EventRepository,
        MessageRepository,
        PushSubscriptionRepository,
        RoutineRepository,
        TaskDefinitionRepository,
        TaskRepository,
        UserRepository,
    )

    user_uuid = UUID(test_user.id)
    # Create repositories
    push_subscription_repo = PushSubscriptionRepository(user_uuid=user_uuid)
    task_repo = TaskRepository(user_uuid=user_uuid)
    day_repo = DayRepository(user_uuid=user_uuid)
    day_template_repo = DayTemplateRepository(user_uuid=user_uuid)
    event_repo = EventRepository(user_uuid=user_uuid)
    message_repo = MessageRepository(user_uuid=user_uuid)
    auth_token_repo = AuthTokenRepository(user_uuid=user_uuid)
    calendar_repo = CalendarRepository(user_uuid=user_uuid)
    routine_repo = RoutineRepository(user_uuid=user_uuid)
    task_definition_repo = TaskDefinitionRepository(user_uuid=user_uuid)
    user_repo = UserRepository()

    # Create gateway adapters
    from planned.infrastructure.gateways.adapters import (
        GoogleCalendarGatewayAdapter,
        WebPushGatewayAdapter,
    )

    google_gateway = GoogleCalendarGatewayAdapter()
    web_push_gateway = WebPushGatewayAdapter()

    # Create services
    calendar_service = CalendarService(
        auth_token_repo=auth_token_repo,
        calendar_repo=calendar_repo,
        event_repo=event_repo,
        google_gateway=google_gateway,
    )

    planning_service = PlanningService(
        user_uuid=user_uuid,
        user_repo=user_repo,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        routine_repo=routine_repo,
        task_definition_repo=task_definition_repo,
        task_repo=task_repo,
    )

    return services.SheppardService(
        day_svc=test_day_svc,
        push_subscription_repo=push_subscription_repo,
        task_repo=task_repo,
        calendar_service=calendar_service,
        planning_service=planning_service,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        web_push_gateway=web_push_gateway,
        push_subscriptions=[],
        mode="idle",
    )


@pytest.fixture
def test_task_today(test_date, test_user):
    from uuid import UUID
    return objects.Task(
        user_uuid=UUID(test_user.id),
        name="Test Task Today",
        status=objects.TaskStatus.READY,
        category=objects.TaskCategory.HOUSE,
        frequency=objects.TaskFrequency.DAILY,
        scheduled_date=test_date,
        task_definition=objects.TaskDefinition(
            user_uuid=UUID(test_user.id),
            id="test-task",
            name="Test Task",
            description="you get the idea",
            type=objects.TaskType.ACTIVITY,
        ),
        schedule=objects.TaskSchedule(
            timing_type=objects.TimingType.DEADLINE,
            start_time=datetime.time(2, 0),
        ),
    )
