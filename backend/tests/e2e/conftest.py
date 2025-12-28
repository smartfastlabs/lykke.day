"""Fixtures for e2e tests - full API tests with test client."""

from datetime import time

import pytest
import pytest_asyncio
from dobles import allow
from fastapi.testclient import TestClient

from planned.app import app
from planned.domain.entities import Alarm, DayTemplate, User
from planned.domain.value_objects.alarm import AlarmType
from planned.domain.value_objects.user import UserSetting
from planned.infrastructure.repositories import DayTemplateRepository, UserRepository
from planned.presentation.middlewares import middlewares


@pytest.fixture(scope="module", autouse=True)
def setup_system_user_day_template():
    """Create DayTemplate for system user before any e2e tests run."""
    import asyncio
    from uuid import UUID, uuid4

    async def _setup():
        user_repo = UserRepository()
        system_user_email = "system@planned.day"
        system_user = await user_repo.get_by_email(system_user_email)

        if system_user is None:
            # Create system user if it doesn't exist
            system_user = User(
                id=str(uuid4()),
                email=system_user_email,
                password_hash="",
                settings=UserSetting(),
            )
            system_user = await user_repo.put(system_user)

        system_user_uuid = UUID(system_user.id)
        day_template_repo = DayTemplateRepository(user_uuid=system_user_uuid)

        # Check if default template exists, create if not
        from planned.core.exceptions import NotFoundError
        try:
            await day_template_repo.get("default")
        except NotFoundError:
            # Template doesn't exist, create it
            default_template = DayTemplate(
                user_uuid=system_user_uuid,
                id="default",
                tasks=[],
                alarm=Alarm(
                    name="Default Alarm",
                    time=time(7, 15),
                    type=AlarmType.FIRM,
                ),
            )
            await day_template_repo.put(default_template)

    # Run the async setup synchronously
    asyncio.run(_setup())


@pytest.fixture
def test_client():
    """FastAPI TestClient for e2e tests."""
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def authenticated_client(test_client):
    """Test client with authenticated session."""
    from uuid import uuid4

    from planned.domain.entities import User
    from planned.domain.value_objects.user import UserSetting
    from planned.infrastructure.repositories import UserRepository
    from planned.infrastructure.utils.dates import get_current_datetime

    # Create a test user
    user_repo = UserRepository()
    user = User(
        id=str(uuid4()),
        email=f"test-{uuid4()}@example.com",
        password_hash="test_hash",
        settings=UserSetting(),
    )
    user = await user_repo.put(user)

    # Set up session for authenticated requests
    # We need to set the password correctly for login
    from passlib.context import CryptContext
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
    from planned.presentation.api.routers.dependencies.user import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user

    yield test_client, user

    # Clean up dependency override
    app.dependency_overrides.clear()


@pytest.fixture
def mock_auth_middleware():
    """Mock auth middleware to bypass authentication."""
    allow(middlewares.auth).mock_for_testing.and_return(True)

