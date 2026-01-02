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
    return InstanceDouble(
        "planned.application.repositories.DayTemplateRepositoryProtocol"
    )


@pytest.fixture
def mock_calendar_entry_repo():
    """Mocked CalendarEntryRepositoryProtocol for unit tests."""
    return InstanceDouble("planned.application.repositories.CalendarEntryRepositoryProtocol")


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
    return InstanceDouble(
        "planned.application.repositories.AuthTokenRepositoryProtocol"
    )


@pytest.fixture
def mock_message_repo():
    """Mocked MessageRepositoryProtocol for unit tests."""
    return InstanceDouble("planned.application.repositories.MessageRepositoryProtocol")


@pytest.fixture
def mock_push_subscription_repo():
    """Mocked PushSubscriptionRepositoryProtocol for unit tests."""
    return InstanceDouble(
        "planned.application.repositories.PushSubscriptionRepositoryProtocol"
    )


@pytest.fixture
def mock_routine_repo():
    """Mocked RoutineRepositoryProtocol for unit tests."""
    return InstanceDouble("planned.application.repositories.RoutineRepositoryProtocol")


@pytest.fixture
def mock_task_definition_repo():
    """Mocked TaskDefinitionRepositoryProtocol for unit tests."""
    return InstanceDouble(
        "planned.application.repositories.TaskDefinitionRepositoryProtocol"
    )


# Mocked gateway fixtures
@pytest.fixture
def mock_google_gateway():
    """Mocked GoogleCalendarGatewayProtocol for unit tests."""
    return InstanceDouble(
        "planned.application.gateways.google_protocol.GoogleCalendarGatewayProtocol"
    )


@pytest.fixture
def mock_web_push_gateway():
    """Mocked WebPushGatewayProtocol for unit tests."""
    return InstanceDouble(
        "planned.application.gateways.web_push_protocol.WebPushGatewayProtocol"
    )


# Mocked service fixtures
@pytest.fixture
def mock_calendar_service():
    """Mocked CalendarService for unit tests."""
    return InstanceDouble("planned.application.services.CalendarService")


@pytest.fixture
def mock_planning_service():
    """Mocked PlanningService for unit tests."""
    return InstanceDouble("planned.application.services.PlanningService")


# Test user UUID fixture
@pytest.fixture
def test_user_id():
    """Test user UUID for unit tests."""
    return uuid4()


# Test user fixture
@pytest.fixture
def test_user(test_user_id):
    """Test user entity for unit tests."""
    from planned.domain.entities import User
    from planned.domain.value_objects.user import UserSetting

    return User(
        id=test_user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=UserSetting(template_defaults=["default"] * 7),
    )


# UnitOfWork fixtures
@pytest.fixture
def mock_uow_factory(
    mock_auth_token_repo,
    mock_calendar_entry_repo,
    mock_calendar_repo,
    mock_day_repo,
    mock_day_template_repo,
    mock_message_repo,
    mock_push_subscription_repo,
    mock_routine_repo,
    mock_task_definition_repo,
    mock_task_repo,
    mock_user_repo,
):
    """Mock UnitOfWorkFactory that returns a mock UnitOfWork with all repositories."""
    from unittest.mock import MagicMock

    class MockUnitOfWork:
        def __init__(self):
            self.auth_tokens = mock_auth_token_repo
            self.calendar_entries = mock_calendar_entry_repo
            self.calendars = mock_calendar_repo
            self.days = mock_day_repo
            self.day_templates = mock_day_template_repo
            self.messages = mock_message_repo
            self.push_subscriptions = mock_push_subscription_repo
            self.routines = mock_routine_repo
            self.task_definitions = mock_task_definition_repo
            self.tasks = mock_task_repo
            self.users = mock_user_repo

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def commit(self):
            pass

        async def rollback(self):
            pass

    class MockUnitOfWorkFactory:
        def create(self, user_id):
            return MockUnitOfWork()

    return MockUnitOfWorkFactory()
