"""Fixtures for unit tests - uses mocked dependencies via dobles."""

from uuid import uuid4

import pytest

from lykke.application.repositories import MessageRepositoryReadOnlyProtocol
from lykke.domain.entities import UserEntity
from lykke.domain.value_objects.user import UserSetting
from tests.support.dobles import (
    create_auth_token_repo_double,
    create_brain_dump_repo_double,
    create_calendar_entry_repo_double,
    create_calendar_entry_series_repo_double,
    create_calendar_repo_double,
    create_day_repo_double,
    create_day_template_repo_double,
    create_google_gateway_double,
    create_pubsub_gateway_double,
    create_push_subscription_repo_double,
    create_repo_double,
    create_routine_definition_repo_double,
    create_routine_repo_double,
    create_tactic_repo_double,
    create_task_definition_repo_double,
    create_task_repo_double,
    create_time_block_definition_repo_double,
    create_trigger_repo_double,
    create_uow_double,
    create_uow_factory_double,
    create_user_repo_double,
    create_web_push_gateway_double,
)


# Mocked repository fixtures
@pytest.fixture
def mock_user_repo():
    """Mocked UserRepositoryReadOnlyProtocol for unit tests."""
    return create_user_repo_double()


@pytest.fixture
def mock_day_repo():
    """Mocked DayRepositoryReadOnlyProtocol for unit tests."""
    return create_day_repo_double()


@pytest.fixture
def mock_day_template_repo():
    """Mocked DayTemplateRepositoryReadOnlyProtocol for unit tests."""
    return create_day_template_repo_double()


@pytest.fixture
def mock_calendar_entry_repo():
    """Mocked CalendarEntryRepositoryReadOnlyProtocol for unit tests."""
    return create_calendar_entry_repo_double()


@pytest.fixture
def mock_calendar_entry_series_repo():
    """Mocked CalendarEntrySeriesRepositoryReadOnlyProtocol for unit tests."""
    return create_calendar_entry_series_repo_double()


@pytest.fixture
def mock_task_repo():
    """Mocked TaskRepositoryReadOnlyProtocol for unit tests."""
    return create_task_repo_double()


@pytest.fixture
def mock_calendar_repo():
    """Mocked CalendarRepositoryReadOnlyProtocol for unit tests."""
    return create_calendar_repo_double()


@pytest.fixture
def mock_auth_token_repo():
    """Mocked AuthTokenRepositoryReadOnlyProtocol for unit tests."""
    return create_auth_token_repo_double()


@pytest.fixture
def mock_push_subscription_repo():
    """Mocked PushSubscriptionRepositoryReadOnlyProtocol for unit tests."""
    return create_push_subscription_repo_double()


@pytest.fixture
def mock_routine_definition_repo():
    """Mocked RoutineDefinitionRepositoryReadOnlyProtocol for unit tests."""
    return create_routine_definition_repo_double()


@pytest.fixture
def mock_routine_repo():
    """Mocked RoutineRepositoryReadOnlyProtocol for unit tests."""
    return create_routine_repo_double()


@pytest.fixture
def mock_task_definition_repo():
    """Mocked TaskDefinitionRepositoryReadOnlyProtocol for unit tests."""
    return create_task_definition_repo_double()


@pytest.fixture
def mock_time_block_definition_repo():
    """Mocked TimeBlockDefinitionRepositoryReadOnlyProtocol for unit tests."""
    return create_time_block_definition_repo_double()


@pytest.fixture
def mock_tactic_repo():
    """Mocked TacticRepositoryReadOnlyProtocol for unit tests."""
    return create_tactic_repo_double()


@pytest.fixture
def mock_trigger_repo():
    """Mocked TriggerRepositoryReadOnlyProtocol for unit tests."""
    return create_trigger_repo_double()


@pytest.fixture
def mock_brain_dump_repo():
    """Mocked BrainDumpRepositoryReadOnlyProtocol for unit tests."""
    return create_brain_dump_repo_double()


@pytest.fixture
def mock_message_repo():
    """Mocked MessageRepositoryReadOnlyProtocol for unit tests."""
    return create_repo_double(MessageRepositoryReadOnlyProtocol)


# Mocked gateway fixtures
@pytest.fixture
def mock_google_gateway():
    """Mocked GoogleCalendarGatewayProtocol for unit tests."""
    return create_google_gateway_double()


@pytest.fixture
def mock_web_push_gateway():
    """Mocked WebPushGatewayProtocol for unit tests."""
    return create_web_push_gateway_double()


@pytest.fixture
def mock_pubsub_gateway():
    """Mocked PubSubGatewayProtocol for unit tests."""
    return create_pubsub_gateway_double()


# Test user UUID fixture
@pytest.fixture
def test_user_id():
    """Test user UUID for unit tests."""
    return uuid4()


# Test user fixture
@pytest.fixture
def test_user(test_user_id):
    """Test user entity for unit tests."""
    return UserEntity(
        id=test_user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=UserSetting(template_defaults=["default"] * 7),
    )


# UnitOfWork fixtures
@pytest.fixture
def mock_uow(
    mock_auth_token_repo,
    mock_calendar_entry_repo,
    mock_calendar_entry_series_repo,
    mock_calendar_repo,
    mock_day_repo,
    mock_day_template_repo,
    mock_message_repo,
    mock_push_subscription_repo,
    mock_routine_definition_repo,
    mock_routine_repo,
    mock_task_definition_repo,
    mock_task_repo,
    mock_user_repo,
    mock_brain_dump_repo,
    mock_time_block_definition_repo,
    mock_tactic_repo,
    mock_trigger_repo,
):
    """Mock UnitOfWork for unit tests."""
    return create_uow_double(
        auth_token_repo=mock_auth_token_repo,
        calendar_entry_repo=mock_calendar_entry_repo,
        calendar_entry_series_repo=mock_calendar_entry_series_repo,
        calendar_repo=mock_calendar_repo,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        message_repo=mock_message_repo,
        push_subscription_repo=mock_push_subscription_repo,
        routine_definition_repo=mock_routine_definition_repo,
        routine_repo=mock_routine_repo,
        tactic_repo=mock_tactic_repo,
        task_definition_repo=mock_task_definition_repo,
        task_repo=mock_task_repo,
        user_repo=mock_user_repo,
        brain_dump_repo=mock_brain_dump_repo,
        time_block_definition_repo=mock_time_block_definition_repo,
        trigger_repo=mock_trigger_repo,
    )


@pytest.fixture
def mock_uow_factory(mock_uow):
    """Mock UnitOfWorkFactory that returns a mock UnitOfWork with all repositories."""
    return create_uow_factory_double(mock_uow)
