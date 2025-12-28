"""Fixtures for unit tests - uses mocked dependencies via dobles."""

from uuid import uuid4

import pytest
from dobles import InstanceDouble


# Mocked repository fixtures
@pytest.fixture
def mock_user_repo():
    """Mocked UserRepositoryProtocol for unit tests."""
    return InstanceDouble("planned.application.repositories.UserRepositoryProtocol")


@pytest.fixture
def mock_day_repo():
    """Mocked DayRepositoryProtocol for unit tests."""
    return InstanceDouble("planned.application.repositories.DayRepositoryProtocol")


@pytest.fixture
def mock_day_template_repo():
    """Mocked DayTemplateRepositoryProtocol for unit tests."""
    return InstanceDouble("planned.application.repositories.DayTemplateRepositoryProtocol")


@pytest.fixture
def mock_event_repo():
    """Mocked EventRepositoryProtocol for unit tests."""
    return InstanceDouble("planned.application.repositories.EventRepositoryProtocol")


@pytest.fixture
def mock_task_repo():
    """Mocked TaskRepositoryProtocol for unit tests."""
    return InstanceDouble("planned.application.repositories.TaskRepositoryProtocol")


@pytest.fixture
def mock_calendar_repo():
    """Mocked CalendarRepositoryProtocol for unit tests."""
    return InstanceDouble("planned.application.repositories.CalendarRepositoryProtocol")


@pytest.fixture
def mock_auth_token_repo():
    """Mocked AuthTokenRepositoryProtocol for unit tests."""
    return InstanceDouble("planned.application.repositories.AuthTokenRepositoryProtocol")


@pytest.fixture
def mock_message_repo():
    """Mocked MessageRepositoryProtocol for unit tests."""
    return InstanceDouble("planned.application.repositories.MessageRepositoryProtocol")


@pytest.fixture
def mock_push_subscription_repo():
    """Mocked PushSubscriptionRepositoryProtocol for unit tests."""
    return InstanceDouble("planned.application.repositories.PushSubscriptionRepositoryProtocol")


@pytest.fixture
def mock_routine_repo():
    """Mocked RoutineRepositoryProtocol for unit tests."""
    return InstanceDouble("planned.application.repositories.RoutineRepositoryProtocol")


@pytest.fixture
def mock_task_definition_repo():
    """Mocked TaskDefinitionRepositoryProtocol for unit tests."""
    return InstanceDouble("planned.application.repositories.TaskDefinitionRepositoryProtocol")


# Mocked gateway fixtures
@pytest.fixture
def mock_google_gateway():
    """Mocked GoogleCalendarGatewayProtocol for unit tests."""
    return InstanceDouble("planned.application.gateways.google_protocol.GoogleCalendarGatewayProtocol")


@pytest.fixture
def mock_web_push_gateway():
    """Mocked WebPushGatewayProtocol for unit tests."""
    return InstanceDouble("planned.application.gateways.web_push_protocol.WebPushGatewayProtocol")


# Test user UUID fixture
@pytest.fixture
def test_user_uuid():
    """Test user UUID for unit tests."""
    return uuid4()

