"""Fixtures for e2e tests - full API tests with test client."""

from datetime import time
from uuid import UUID, uuid4

import pytest
from dobles import allow
from fastapi.testclient import TestClient
from passlib.context import CryptContext

from planned.app import app
from planned.core.exceptions import NotFoundError
from planned.domain.entities import Alarm, DayTemplate, User
from planned.domain.value_objects.alarm import AlarmType
from planned.domain.value_objects.user import UserSetting
from planned.infrastructure.database.utils import reset_engine
from planned.infrastructure.repositories import DayTemplateRepository, UserRepository
from planned.presentation.api.routers.dependencies.user import get_current_user
from planned.presentation.middlewares import middlewares


@pytest.fixture
def setup_test_user_day_template():
    """Fixture that returns a function to create a test user with DayTemplate."""

    async def _setup():
        """Create a test user with default DayTemplate."""

        user_repo = UserRepository()
        test_user_email = f"test_{uuid4()}@planned.day"
        test_user = User(
            id=str(uuid4()),
            email=test_user_email,
            password_hash="",
            settings=UserSetting(),
        )
        test_user = await user_repo.put(test_user)

        test_user_uuid = UUID(test_user.id)
        day_template_repo = DayTemplateRepository(user_uuid=test_user_uuid)

        # Check if default template exists, create if not
        try:
            await day_template_repo.get("default")
        except NotFoundError:
            # Template doesn't exist, create it
            default_template = DayTemplate(
                user_uuid=test_user_uuid,
                id="default",
                tasks=[],
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

        # Set up session for authenticated requests
        # We need to set the password correctly for login
        user_repo = UserRepository()
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        user.password_hash = pwd_context.hash("test_password")
        user = await user_repo.put(user)

        # Login to set up the session
        response = test_client.put(
            "/auth/login",
            json={"email": user.email, "password": "test_password"},
        )
        assert response.status_code == 200, f"Login failed: {response.text}"

        # Mock the middleware to bypass auth checks
        allow(middlewares.auth).mock_for_testing.and_return(True)

        # Override get_current_user dependency to return our test user
        # This is needed because get_current_user checks the session directly,
        # and TestClient doesn't preserve sessions reliably
        app.dependency_overrides[get_current_user] = lambda: user

        return test_client, user

    return _authenticated_client


@pytest.fixture
def mock_auth_middleware():
    """Mock auth middleware to bypass authentication."""
    allow(middlewares.auth).mock_for_testing.and_return(True)
