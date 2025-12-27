import asyncio
import datetime
import os
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
async def clear_repos():
    """Clear all data from the database."""
    from sqlalchemy import text

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
def test_client():
    # Make a request that sets up the session, then modify it
    with TestClient(app) as client:
        allow(middlewares.auth).mock_for_testing.and_return(True)
        yield client


@pytest.fixture
def test_deleted_event(test_date_tomorrow):
    starts_at = datetime.datetime.combine(
        test_date_tomorrow,
        datetime.time(hour=2),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    )
    return objects.Event(
        name="Test Event",
        calendar_id="test-calendar",
        platform_id="test-id",
        platform="testing",
        status="cancelled",
        starts_at=starts_at,
    )


@pytest.fixture
def test_event(test_date_tomorrow):
    starts_at = datetime.datetime.combine(
        test_date_tomorrow,
        datetime.time(hour=2),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    )

    return objects.Event(
        name="Test Event",
        frequency="ONCE",
        calendar_id="test-calendar",
        platform_id="test-id",
        platform="testing",
        status="status",
        starts_at=starts_at,
    )


@pytest.fixture
def test_event_today(test_date):
    starts_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=2),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    )

    return objects.Event(
        name="Test Event",
        frequency="ONCE",
        calendar_id="test-calendar",
        platform_id="test-id",
        platform="testing",
        status="status",
        starts_at=starts_at,
    )


@pytest.fixture
def test_calendar(test_auth_token):
    return objects.Calendar(
        name="Test Calendar",
        auth_token_id=test_auth_token.id,
        platform="google",
        platform_id="platform_id",
    )


@pytest.fixture
def test_auth_token():
    return objects.AuthToken(
        platform="testing",
        platform_id="test-auth-token",
        token="token",
    )


@pytest.fixture
def test_day(test_date):
    return objects.Day(
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


@pytest.fixture
def test_day_svc(test_day_ctx):
    from planned.infrastructure.repositories import (
        DayRepository,
        DayTemplateRepository,
        EventRepository,
        MessageRepository,
        TaskRepository,
    )

    day_repo = DayRepository()
    day_template_repo = DayTemplateRepository()
    event_repo = EventRepository()
    message_repo = MessageRepository()
    task_repo = TaskRepository()

    return services.DayService(
        ctx=test_day_ctx,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
    )


@pytest.fixture
def test_sheppard_svc(test_day_svc):
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
    )

    # Create repositories
    push_subscription_repo = PushSubscriptionRepository()
    task_repo = TaskRepository()
    day_repo = DayRepository()
    day_template_repo = DayTemplateRepository()
    event_repo = EventRepository()
    message_repo = MessageRepository()
    auth_token_repo = AuthTokenRepository()
    calendar_repo = CalendarRepository()
    routine_repo = RoutineRepository()
    task_definition_repo = TaskDefinitionRepository()

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
def test_task_today(test_date):
    return objects.Task(
        name="Test Task Today",
        status=objects.TaskStatus.READY,
        category=objects.TaskCategory.HOUSE,
        frequency=objects.TaskFrequency.DAILY,
        scheduled_date=test_date,
        task_definition=objects.TaskDefinition(
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
