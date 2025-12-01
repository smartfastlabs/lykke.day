import datetime
import shutil
import tempfile
from uuid import uuid4

import pytest
from dobles import allow
from fastapi.testclient import TestClient
from freezegun import freeze_time

from planned import middlewares, objects, settings
from planned.app import app
from planned.utils.dates import get_current_date, get_current_datetime


@pytest.fixture
def today():
    return get_current_date()


@pytest.fixture
def test_date():
    with freeze_time("2025-11-27 00:00:00-6:00"):
        yield datetime.date(2025, 11, 27)


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
def test_deleted_event(test_date):
    return objects.Event(
        name="Test Event",
        calendar_id="test-calendar",
        platform_id="test-id",
        platform="testing",
        status="cancelled",
        starts_at=test_date + datetime.timedelta(hours=2),
    )


@pytest.fixture
def test_event(test_date):
    return objects.Event(
        name="Test Event",
        calendar_id="test-calendar",
        platform_id="test-id",
        platform="testing",
        status="status",
        starts_at=test_date + datetime.timedelta(days=2),
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
