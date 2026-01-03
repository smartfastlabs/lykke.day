"""Fixtures for e2e tests - full API tests with test client."""

from datetime import time
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from planned.app import app
from planned.domain.entities import DayTemplate
from planned.domain.entities import User as UserEntity
from planned.domain.value_objects.alarm import Alarm, AlarmType
from planned.domain.value_objects.user import UserSetting
from planned.infrastructure.database.tables import User as UserDB
from planned.infrastructure.database.utils import reset_engine
from planned.infrastructure.repositories import DayTemplateRepository, UserRepository
from planned.presentation.api.routers.dependencies.user import get_current_user


@pytest.fixture
def setup_test_user_day_template():
    """Fixture that returns a function to create a test user with DayTemplate."""

    async def _setup():
        """Create a test user with default DayTemplate."""
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        user_repo = UserRepository()
        test_user_email = f"test_{uuid4()}@planned.day"
        test_user = UserEntity(
            email=test_user_email,
            hashed_password=pwd_context.hash("test_password"),
            settings=UserSetting(),
        )
        test_user = await user_repo.put(test_user)

        test_user_id = test_user.id
        day_template_repo = DayTemplateRepository(user_id=test_user_id)

        # Create default template (UUID will be auto-generated)
        default_template = DayTemplate(
            user_id=test_user_id,
            slug="default",
            alarm=Alarm(
                name="Default Alarm",
                time=time(7, 15),
                type=AlarmType.FIRM,
            ),
        )
        await day_template_repo.put(default_template)
        return test_user

    return _setup


@pytest.fixture
def test_client():
    """FastAPI TestClient for e2e tests."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def authenticated_client(test_client, setup_test_user_day_template, request):
    """Test client with authenticated session."""

    # Register cleanup finalizer
    def cleanup():
        app.dependency_overrides.clear()

    request.addfinalizer(cleanup)

    async def _authenticated_client():
        """Return authenticated test client and user."""
        # Use setup_test_user_day_template to create user and default template
        await reset_engine()
        user = await setup_test_user_day_template()

        # Override get_current_user dependency to return our test user
        # This bypasses the actual authentication for testing
        app.dependency_overrides[get_current_user] = lambda: user

        return test_client, user

    return _authenticated_client
