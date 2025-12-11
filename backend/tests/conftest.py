import datetime
import shutil
import tempfile
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from dobles import allow
from fastapi.testclient import TestClient
from freezegun import freeze_time

from planned import middlewares, objects, services, settings
from planned.app import app
from planned.utils.dates import get_current_date, get_current_datetime


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


@pytest.fixture(autouse=True)
def clear_repos():
    old_value = settings.DATA_PATH
    with tempfile.TemporaryDirectory() as temp_dir:
        # Recursively copy *contents* of ./tests/data into temp_dir
        shutil.copytree(
            "./tests/data",
            temp_dir,
            dirs_exist_ok=True,  # allows temp_dir to already exist
        )

        try:
            settings.DATA_PATH = temp_dir
            yield
        finally:
            settings.DATA_PATH = old_value


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
    return services.DayService(test_day_ctx)


@pytest.fixture
def test_sheppard_svc(test_day_svc):
    return services.SheppardService(
        day_svc=test_day_svc,
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
