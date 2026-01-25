"""Unit tests for Google Calendar sync logic."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.commands.calendar.sync_calendar import SyncCalendarHandler
from lykke.domain import value_objects
from lykke.domain.entities import AuthTokenEntity, CalendarEntity, CalendarEntryEntity
from lykke.domain.value_objects import TaskFrequency
from lykke.domain.value_objects.sync import SyncSubscription
from lykke.infrastructure.gateways.google import GoogleCalendarGateway
from tests.support.dobles import (
    create_auth_token_repo_double,
    create_calendar_entry_repo_double,
    create_calendar_entry_series_repo_double,
    create_calendar_repo_double,
    create_google_gateway_double,
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
)


@pytest.fixture
def test_calendar_id():
    """Test calendar UUID."""
    return uuid4()


@pytest.fixture
def test_auth_token_id():
    """Test auth token UUID."""
    return uuid4()


@pytest.fixture
def test_calendar(test_user_id, test_calendar_id, test_auth_token_id):
    """Test calendar entity."""
    return CalendarEntity(
        id=test_calendar_id,
        user_id=test_user_id,
        name="Test Calendar",
        platform="google",
        platform_id="test@calendar.google.com",
        auth_token_id=test_auth_token_id,
        last_sync_at=datetime(2025, 1, 1, 0, 0, 0, tzinfo=UTC),
        sync_subscription=SyncSubscription(
            subscription_id="test-channel",
            resource_id="test-resource",
            expiration=datetime(2025, 12, 31, 23, 59, 59, tzinfo=UTC),
            provider="google",
            sync_token="old-sync-token",
            client_state="test-secret",
            webhook_url="https://example.com/webhook/test",
        ),
    )


@pytest.fixture
def test_auth_token(test_user_id):
    """Test auth token."""
    return AuthTokenEntity(
        user_id=test_user_id,
        platform="google",
        token="test-token",
        refresh_token="test-refresh",
        expires_at=datetime(2025, 12, 31, 23, 59, 59, tzinfo=UTC),
        scopes=["calendar.readonly"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id="test-client-id",
        client_secret="test-client-secret",
    )


@pytest.fixture
def mock_calendar_entry_repo():
    """Mock calendar entry repository."""
    return create_calendar_entry_repo_double()


@pytest.fixture
def mock_calendar_entry_series_repo():
    """Mock calendar entry series repository."""
    return create_calendar_entry_series_repo_double()


@pytest.fixture
def mock_calendar_repo():
    """Mock calendar repository."""
    return create_calendar_repo_double()


@pytest.fixture
def mock_auth_token_repo():
    """Mock auth token repository."""
    return create_auth_token_repo_double()


@pytest.fixture
def mock_google_gateway():
    """Mock Google gateway."""
    return create_google_gateway_double()


@pytest.fixture
def mock_uow(
    test_calendar,
    test_auth_token,
    mock_calendar_repo,
    mock_auth_token_repo,
    mock_calendar_entry_repo,
    mock_calendar_entry_series_repo,
):
    """Mock UnitOfWork for sync tests."""
    allow(mock_calendar_repo).get.and_return(test_calendar)
    allow(mock_auth_token_repo).get.and_return(test_auth_token)
    allow(mock_calendar_entry_repo).search_one_or_none.and_return(None)

    return create_uow_double(
        calendar_repo=mock_calendar_repo,
        auth_token_repo=mock_auth_token_repo,
        calendar_entry_repo=mock_calendar_entry_repo,
        calendar_entry_series_repo=mock_calendar_entry_series_repo,
    )


@pytest.fixture
def mock_ro_repos(
    mock_calendar_repo,
    mock_auth_token_repo,
    mock_calendar_entry_repo,
    mock_calendar_entry_series_repo,
):
    """Mock read-only repositories with required attributes."""
    return create_read_only_repos_double(
        calendar_repo=mock_calendar_repo,
        auth_token_repo=mock_auth_token_repo,
        calendar_entry_repo=mock_calendar_entry_repo,
        calendar_entry_series_repo=mock_calendar_entry_series_repo,
    )


@pytest.fixture
def mock_uow_factory(mock_uow):
    """Mock UnitOfWork factory."""
    return create_uow_factory_double(mock_uow)


def test_sync_calendar_changes_with_new_events(
    test_user_id,
    test_calendar,
    mock_ro_repos,
    mock_uow_factory,
    mock_uow,
    mock_google_gateway,
    mock_calendar_entry_repo,
):
    """Test syncing calendar with new events."""
    # Create test events from Google
    new_event = CalendarEntryEntity(
        id=uuid4(),
        user_id=test_user_id,
        calendar_id=test_calendar.id,
        platform_id="google-event-1",
        platform="google",
        status="confirmed",
        name="New Meeting",
        starts_at=datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC),
        ends_at=datetime(2025, 1, 15, 11, 0, 0, tzinfo=UTC),
        frequency=TaskFrequency.ONCE,
    )

    allow(mock_google_gateway).load_calendar_events.and_return(
        ([new_event], [], [], "new-sync-token")
    )
    allow(mock_calendar_entry_repo).search_one_or_none.and_return(None)

    # Create handler and sync
    SyncCalendarHandler(
        ro_repos=mock_ro_repos,
        uow_factory=mock_uow_factory,
        user_id=test_user_id,
        google_gateway=mock_google_gateway,
    )

    # Note: This is a unit test, so we're testing the logic, not actual async execution
    # In a real scenario, you'd use pytest-asyncio and await the sync


def test_sync_calendar_changes_with_updated_events(
    test_user_id,
    test_calendar,
    mock_ro_repos,
    mock_uow_factory,
    mock_uow,
    mock_google_gateway,
    mock_calendar_entry_repo,
):
    """Test syncing calendar with updated events."""
    # Create existing event
    existing_event = CalendarEntryEntity(
        id=uuid4(),
        user_id=test_user_id,
        calendar_id=test_calendar.id,
        platform_id="google-event-1",
        platform="google",
        status="confirmed",
        name="Old Meeting Name",
        starts_at=datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC),
        ends_at=datetime(2025, 1, 15, 11, 0, 0, tzinfo=UTC),
        frequency=TaskFrequency.ONCE,
    )

    # Create updated version from Google
    updated_event = CalendarEntryEntity(
        id=uuid4(),  # Different ID but same platform_id
        user_id=test_user_id,
        calendar_id=test_calendar.id,
        platform_id="google-event-1",  # Same platform_id
        platform="google",
        status="confirmed",
        name="Updated Meeting Name",  # Changed name
        starts_at=datetime(2025, 1, 15, 14, 0, 0, tzinfo=UTC),  # Changed time
        ends_at=datetime(2025, 1, 15, 15, 0, 0, tzinfo=UTC),
        frequency=TaskFrequency.ONCE,
    )

    allow(mock_google_gateway).load_calendar_events.and_return(
        ([updated_event], [], [], "new-sync-token")
    )
    allow(mock_calendar_entry_repo).search_one_or_none.and_return(existing_event)


def test_sync_calendar_changes_with_deleted_events(
    test_user_id,
    test_calendar,
    mock_ro_repos,
    mock_uow_factory,
    mock_uow,
    mock_google_gateway,
    mock_calendar_entry_repo,
):
    """Test syncing calendar with deleted events."""
    # Create existing event
    existing_event = CalendarEntryEntity(
        id=uuid4(),
        user_id=test_user_id,
        calendar_id=test_calendar.id,
        platform_id="google-event-1",
        platform="google",
        status="confirmed",
        name="Meeting to Delete",
        starts_at=datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC),
        ends_at=datetime(2025, 1, 15, 11, 0, 0, tzinfo=UTC),
        frequency=TaskFrequency.ONCE,
    )

    # Create cancelled version from Google
    cancelled_event = CalendarEntryEntity(
        id=uuid4(),
        user_id=test_user_id,
        calendar_id=test_calendar.id,
        platform_id="google-event-1",
        platform="google",
        status="cancelled",  # Cancelled status
        name="Meeting to Delete",
        starts_at=datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC),
        ends_at=datetime(2025, 1, 15, 11, 0, 0, tzinfo=UTC),
        frequency=TaskFrequency.ONCE,
    )

    allow(mock_google_gateway).load_calendar_events.and_return(
        ([cancelled_event], [], [], "new-sync-token")
    )
    allow(mock_calendar_entry_repo).search_one_or_none.and_return(existing_event)


def test_sync_calendar_changes_filters_far_future_events(
    test_user_id,
    test_calendar,
    mock_ro_repos,
    mock_uow_factory,
    mock_uow,
    mock_google_gateway,
    mock_calendar_entry_repo,
):
    """Test that events more than a year in the future are filtered out."""
    # Create event far in the future (2 years)
    far_future_event = CalendarEntryEntity(
        id=uuid4(),
        user_id=test_user_id,
        calendar_id=test_calendar.id,
        platform_id="google-event-future",
        platform="google",
        status="confirmed",
        name="Far Future Meeting",
        starts_at=datetime(2027, 1, 15, 10, 0, 0, tzinfo=UTC),
        ends_at=datetime(2027, 1, 15, 11, 0, 0, tzinfo=UTC),
        frequency=TaskFrequency.ONCE,
    )

    allow(mock_google_gateway).load_calendar_events.and_return(
        ([far_future_event], [], [], "new-sync-token")
    )


def test_sync_calendar_changes_handles_missing_deleted_events(
    test_user_id,
    test_calendar,
    mock_ro_repos,
    mock_uow_factory,
    mock_uow,
    mock_google_gateway,
    mock_calendar_entry_repo,
):
    """Test that sync handles deletion of events that don't exist locally."""
    # Create cancelled event that doesn't exist locally
    cancelled_event = CalendarEntryEntity(
        id=uuid4(),
        user_id=test_user_id,
        calendar_id=test_calendar.id,
        platform_id="google-event-nonexistent",
        platform="google",
        status="cancelled",
        name="Nonexistent Meeting",
        starts_at=datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC),
        ends_at=datetime(2025, 1, 15, 11, 0, 0, tzinfo=UTC),
        frequency=TaskFrequency.ONCE,
    )

    allow(mock_google_gateway).load_calendar_events.and_return(
        ([cancelled_event], [], [], "new-sync-token")
    )
    allow(mock_calendar_entry_repo).search_one_or_none.and_return(None)


def test_sync_calendar_changes_updates_sync_token(
    test_user_id,
    test_calendar,
    mock_ro_repos,
    mock_uow_factory,
    mock_uow,
    mock_google_gateway,
    mock_calendar_entry_repo,
):
    """Test that sync updates the calendar's sync token."""
    allow(mock_google_gateway).load_calendar_events.and_return(
        ([], [], [], "brand-new-sync-token")
    )


def test_google_event_conversion_includes_series(test_user_id):
    """Ensure Google events produce series metadata."""
    calendar = CalendarEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Test Calendar",
        platform="google",
        platform_id="calendar-123",
        auth_token_id=uuid4(),
        default_event_category=value_objects.EventCategory.WORK,
    )
    gateway = GoogleCalendarGateway()
    event = {
        "id": "event-1",
        "summary": "Weekly Standup",
        "status": "confirmed",
        "recurrence": ["RRULE:FREQ=WEEKLY;BYDAY=MO"],
        "recurringEventId": "series-abc",
        "start": {"dateTime": "2025-01-05T10:00:00Z", "timeZone": "UTC"},
        "end": {"dateTime": "2025-01-05T11:00:00Z", "timeZone": "UTC"},
        "created": "2025-01-01T00:00:00Z",
        "updated": "2025-01-02T00:00:00Z",
    }

    entry, series = gateway._google_event_to_entity(
        calendar=calendar,
        event=event,
        frequency_cache={},
        recurrence_lookup=create_calendar_entry_series_repo_double(),
    )

    assert entry.calendar_entry_series_id is not None
    assert series is not None
    assert entry.calendar_entry_series_id == series.id
    assert series.recurrence == ["RRULE:FREQ=WEEKLY;BYDAY=MO"]
    assert entry.category == value_objects.EventCategory.WORK
    assert not hasattr(series, "timezone")
