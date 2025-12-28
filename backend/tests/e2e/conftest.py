"""Fixtures for e2e tests - full API tests with test client."""

from fastapi.testclient import TestClient

import pytest
import pytest_asyncio
from dobles import allow

from planned.app import app
from planned.infrastructure.utils.dates import get_current_datetime
from planned.presentation.middlewares import middlewares


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
    
    # Create a test user
    user_repo = UserRepository()
    user = User(
        id=str(uuid4()),
        email=f"test-{uuid4()}@example.com",
        password_hash="test_hash",
        settings=UserSetting(),
    )
    user = await user_repo.put(user)
    
    # Mock the auth middleware to allow requests
    allow(middlewares.auth).mock_for_testing.and_return(True)
    
    # Set up session data
    with test_client.session_transaction() as session:
        session["user_uuid"] = str(user.id)
        session["logged_in_at"] = str(get_current_datetime())
    
    yield test_client, user


@pytest.fixture
def mock_auth_middleware():
    """Mock auth middleware to bypass authentication."""
    allow(middlewares.auth).mock_for_testing.and_return(True)

