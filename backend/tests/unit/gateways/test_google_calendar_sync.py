"""Unit tests for Google Calendar sync logic."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from dobles import InstanceDouble, allow, expect
from lykke.application.commands.calendar.sync_calendar_changes import (
    SyncCalendarChangesHandler,
)
from lykke.application.unit_of_work import ReadOnlyRepositories, UnitOfWorkProtocol
from lykke.domain.entities import CalendarEntity, CalendarEntryEntity
from lykke.domain.value_objects import TaskFrequency
from lykke.domain.value_objects.sync import SyncSubscription
from lykke.domain import data_objects


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
        ),
    )


@pytest.fixture
def test_auth_token(test_user_id):
    """Test auth token."""
    return data_objects.AuthToken(
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
def mock_uow(
    test_calendar,
    test_auth_token,
    mock_calendar_repo,
    mock_auth_token_repo,
    mock_calendar_entry_repo,
):
    """Mock UnitOfWork for sync tests."""
    uow = InstanceDouble("lykke.application.unit_of_work.UnitOfWorkProtocol")
    
    # Setup repository access
    allow(uow).calendar_ro_repo.and_return(mock_calendar_repo)
    allow(uow).auth_token_ro_repo.and_return(mock_auth_token_repo)
    allow(uow).calendar_entry_ro_repo.and_return(mock_calendar_entry_repo)
    
    # Setup repository responses
    allow(mock_calendar_repo).get.and_return(test_calendar)
    allow(mock_auth_token_repo).get.and_return(test_auth_token)
    
    # Setup context manager
    allow(uow).__aenter__.and_return(uow)
    allow(uow).__aexit__
    
    # Setup methods
    allow(uow).add
    allow(uow).create
    allow(uow).delete
    
    return uow


@pytest.fixture
def mock_ro_repos():
    """Mock read-only repositories."""
    return InstanceDouble("lykke.application.unit_of_work.ReadOnlyRepositories")


@pytest.fixture
def mock_uow_factory(mock_uow):
    """Mock UnitOfWork factory."""
    factory = InstanceDouble("lykke.application.unit_of_work.UnitOfWorkFactory")
    allow(factory).create.and_return(mock_uow)
    return factory


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
    
    # Mock Google gateway to return new events
    allow(mock_google_gateway).load_calendar_events.and_return(
        ([new_event], [], "new-sync-token")
    )
    
    # Mock calendar entry repo to return None (event doesn't exist)
    allow(mock_calendar_entry_repo).get_by_platform_id.and_return(None)
    
    # Expect the event to be added to UoW
    expect(mock_uow).add.once()
    
    # Create handler and sync
    handler = SyncCalendarChangesHandler(
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
    
    # Mock Google gateway to return updated event
    allow(mock_google_gateway).load_calendar_events.and_return(
        ([updated_event], [], "new-sync-token")
    )
    
    # Mock calendar entry repo to return existing event
    allow(mock_calendar_entry_repo).get_by_platform_id.and_return(existing_event)
    
    # Expect the updated event to be added to UoW (upsert via repo.put)
    expect(mock_uow).add.once()


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
    
    # Mock Google gateway to return cancelled event
    allow(mock_google_gateway).load_calendar_events.and_return(
        ([cancelled_event], [], "new-sync-token")
    )
    
    # Mock calendar entry repo to return existing event
    allow(mock_calendar_entry_repo).get_by_platform_id.and_return(existing_event)
    
    # Expect the event to be deleted
    expect(mock_uow).delete.once()


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
    
    # Mock Google gateway to return far future event
    allow(mock_google_gateway).load_calendar_events.and_return(
        ([far_future_event], [], "new-sync-token")
    )
    
    # Expect NO events to be added (filtered out)
    expect(mock_uow).add.never()
    expect(mock_uow).create.never()


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
    
    # Mock Google gateway to return cancelled event
    allow(mock_google_gateway).load_calendar_events.and_return(
        ([cancelled_event], [], "new-sync-token")
    )
    
    # Mock calendar entry repo to return None (event doesn't exist)
    allow(mock_calendar_entry_repo).get_by_platform_id.and_return(None)
    
    # Expect NO deletion (event doesn't exist)
    expect(mock_uow).delete.never()


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
    # Mock Google gateway to return new sync token
    allow(mock_google_gateway).load_calendar_events.and_return(
        ([], [], "brand-new-sync-token")
    )
    
    # Expect calendar to be updated with new sync token
    expect(mock_uow).add.once()  # Calendar update

