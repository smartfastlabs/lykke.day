"""Fixtures for unit tests - uses mocked dependencies via dobles."""

from uuid import uuid4

import pytest
from dobles import InstanceDouble


# Mocked repository fixtures
@pytest.fixture
def mock_user_repo():
    """Mocked UserRepositoryReadOnlyProtocol for unit tests."""
    return InstanceDouble(
        "lykke.application.repositories.UserRepositoryReadOnlyProtocol"
    )


@pytest.fixture
def mock_day_repo():
    """Mocked DayRepositoryReadOnlyProtocol for unit tests."""
    return InstanceDouble("lykke.application.repositories.DayRepositoryReadOnlyProtocol")


@pytest.fixture
def mock_day_template_repo():
    """Mocked DayTemplateRepositoryReadOnlyProtocol for unit tests."""
    return InstanceDouble(
        "lykke.application.repositories.DayTemplateRepositoryReadOnlyProtocol"
    )


@pytest.fixture
def mock_calendar_entry_repo():
    """Mocked CalendarEntryRepositoryReadOnlyProtocol for unit tests."""
    return InstanceDouble(
        "lykke.application.repositories.CalendarEntryRepositoryReadOnlyProtocol"
    )


@pytest.fixture
def mock_task_repo():
    """Mocked TaskRepositoryReadOnlyProtocol for unit tests."""
    return InstanceDouble("lykke.application.repositories.TaskRepositoryReadOnlyProtocol")


@pytest.fixture
def mock_calendar_repo():
    """Mocked CalendarRepositoryReadOnlyProtocol for unit tests."""
    return InstanceDouble(
        "lykke.application.repositories.CalendarRepositoryReadOnlyProtocol"
    )


@pytest.fixture
def mock_auth_token_repo():
    """Mocked AuthTokenRepositoryReadOnlyProtocol for unit tests."""
    return InstanceDouble(
        "lykke.application.repositories.AuthTokenRepositoryReadOnlyProtocol"
    )


@pytest.fixture
def mock_push_subscription_repo():
    """Mocked PushSubscriptionRepositoryReadOnlyProtocol for unit tests."""
    return InstanceDouble(
        "lykke.application.repositories.PushSubscriptionRepositoryReadOnlyProtocol"
    )


@pytest.fixture
def mock_routine_repo():
    """Mocked RoutineRepositoryReadOnlyProtocol for unit tests."""
    return InstanceDouble("lykke.application.repositories.RoutineRepositoryReadOnlyProtocol")


@pytest.fixture
def mock_task_definition_repo():
    """Mocked TaskDefinitionRepositoryReadOnlyProtocol for unit tests."""
    return InstanceDouble(
        "lykke.application.repositories.TaskDefinitionRepositoryReadOnlyProtocol"
    )


# Mocked gateway fixtures
@pytest.fixture
def mock_google_gateway():
    """Mocked GoogleCalendarGatewayProtocol for unit tests."""
    return InstanceDouble(
        "lykke.application.gateways.google_protocol.GoogleCalendarGatewayProtocol"
    )


@pytest.fixture
def mock_web_push_gateway():
    """Mocked WebPushGatewayProtocol for unit tests."""
    return InstanceDouble(
        "lykke.application.gateways.web_push_protocol.WebPushGatewayProtocol"
    )


# Test user UUID fixture
@pytest.fixture
def test_user_id():
    """Test user UUID for unit tests."""
    return uuid4()


# Test user fixture
@pytest.fixture
def test_user(test_user_id):
    """Test user entity for unit tests."""
    from lykke.domain.entities import UserEntity
    from lykke.domain.value_objects.user import UserSetting

    return UserEntity(
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
