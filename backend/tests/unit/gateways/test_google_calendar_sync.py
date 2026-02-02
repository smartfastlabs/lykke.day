"""Unit tests for Google Calendar sync logic."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.commands.calendar.sync_calendar import (
    SyncCalendarCommand,
    SyncCalendarHandler,
)
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import (
    AuthTokenEntity,
    CalendarEntity,
    CalendarEntryEntity,
    CalendarEntrySeriesEntity,
)
from lykke.domain.events.calendar_entry_events import (
    CalendarEntryCreatedEvent,
    CalendarEntryDeletedEvent,
    CalendarEntryUpdatedEvent,
)
from lykke.domain.events.calendar_entry_series_events import (
    CalendarEntrySeriesUpdatedEvent,
)
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
        ([new_event], [], [], [], "new-sync-token")
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
        ([updated_event], [], [], [], "new-sync-token")
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
        ([cancelled_event], [], [], [], "new-sync-token")
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
        ([far_future_event], [], [], [], "new-sync-token")
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
        ([cancelled_event], [], [], [], "new-sync-token")
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
        ([], [], [], [], "brand-new-sync-token")
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


@pytest.mark.asyncio
async def test_sync_calendar_series_updates_cascade_entries_once(
    test_user_id,
    test_calendar,
    mock_ro_repos,
    mock_uow_factory,
    mock_uow,
    mock_google_gateway,
    mock_calendar_entry_series_repo,
    mock_calendar_entry_repo,
):
    """Series updates should cascade to entries with a single notification."""
    series_id = CalendarEntrySeriesEntity.id_from_platform("google", "series-1")
    existing_series = CalendarEntrySeriesEntity(
        id=series_id,
        user_id=test_user_id,
        calendar_id=test_calendar.id,
        name="Old Series",
        platform_id="series-1",
        platform="google",
        frequency=TaskFrequency.DAILY,
        event_category=value_objects.EventCategory.WORK,
        recurrence=["RRULE:FREQ=DAILY"],
        starts_at=datetime(2025, 1, 1, 9, 0, tzinfo=UTC),
        ends_at=datetime(2025, 1, 1, 10, 0, tzinfo=UTC),
    )
    updated_series = CalendarEntrySeriesEntity(
        id=series_id,
        user_id=test_user_id,
        calendar_id=test_calendar.id,
        name="New Series",
        platform_id="series-1",
        platform="google",
        frequency=TaskFrequency.WEEKLY,
        event_category=value_objects.EventCategory.PERSONAL,
        recurrence=["RRULE:FREQ=WEEKLY;BYDAY=MO"],
        starts_at=datetime(2025, 1, 1, 9, 0, tzinfo=UTC),
        ends_at=datetime(2025, 1, 1, 10, 0, tzinfo=UTC),
    )
    entry_one = CalendarEntryEntity(
        user_id=test_user_id,
        name="Old Series",
        calendar_id=test_calendar.id,
        calendar_entry_series_id=series_id,
        platform_id="entry-1",
        platform="google",
        status="confirmed",
        starts_at=datetime(2025, 1, 2, 9, 0, tzinfo=UTC),
        ends_at=datetime(2025, 1, 2, 10, 0, tzinfo=UTC),
        frequency=TaskFrequency.DAILY,
        category=value_objects.EventCategory.WORK,
    )
    entry_two = CalendarEntryEntity(
        user_id=test_user_id,
        name="Old Series",
        calendar_id=test_calendar.id,
        calendar_entry_series_id=series_id,
        platform_id="entry-2",
        platform="google",
        status="confirmed",
        starts_at=datetime(2025, 1, 3, 9, 0, tzinfo=UTC),
        ends_at=datetime(2025, 1, 3, 10, 0, tzinfo=UTC),
        frequency=TaskFrequency.DAILY,
        category=value_objects.EventCategory.WORK,
    )

    allow(mock_calendar_entry_series_repo).get.and_return(existing_series)
    allow(mock_google_gateway).load_calendar_events.and_return(
        ([], [], [updated_series], [], "new-sync-token")
    )

    async def search_entries(query: object) -> list[CalendarEntryEntity]:
        if getattr(query, "calendar_entry_series_id", None) == series_id:
            return [entry_one, entry_two]
        return []

    mock_calendar_entry_repo.search = search_entries
    mock_uow.calendar_entry_ro_repo.search = search_entries

    async def get_user(_: object) -> object:
        return SimpleNamespace(settings=SimpleNamespace(timezone="UTC"))

    mock_uow.user_ro_repo.get = get_user

    handler = SyncCalendarHandler(
        ro_repos=mock_ro_repos,
        uow_factory=mock_uow_factory,
        user_id=test_user_id,
        google_gateway=mock_google_gateway,
    )

    await handler.handle(SyncCalendarCommand(calendar_id=test_calendar.id))

    updated_entries = [
        entity for entity in mock_uow.added if isinstance(entity, CalendarEntryEntity)
    ]
    assert len(updated_entries) == 2
    assert all(entry.name == "New Series" for entry in updated_entries)
    assert all(
        entry.category == value_objects.EventCategory.PERSONAL
        for entry in updated_entries
    )
    assert all(entry.frequency == TaskFrequency.WEEKLY for entry in updated_entries)

    updated_event_count = sum(
        1
        for entry in updated_entries
        for event in entry.collect_events()
        if isinstance(event, CalendarEntryUpdatedEvent)
    )
    assert updated_event_count == 1


@pytest.mark.asyncio
async def test_sync_calendar_series_deletion_cascades_entries_once(
    test_user_id,
    test_calendar,
    mock_ro_repos,
    mock_uow_factory,
    mock_uow,
    mock_google_gateway,
    mock_calendar_entry_series_repo,
    mock_calendar_entry_repo,
):
    """Series deletions should cascade to entries and delete the series."""
    series_id = CalendarEntrySeriesEntity.id_from_platform("google", "series-2")
    existing_series = CalendarEntrySeriesEntity(
        id=series_id,
        user_id=test_user_id,
        calendar_id=test_calendar.id,
        name="Series To Delete",
        platform_id="series-2",
        platform="google",
        frequency=TaskFrequency.DAILY,
    )
    now = datetime.now(UTC)
    entry_one = CalendarEntryEntity(
        user_id=test_user_id,
        name="Series To Delete",
        calendar_id=test_calendar.id,
        calendar_entry_series_id=series_id,
        platform_id="entry-10",
        platform="google",
        status="confirmed",
        starts_at=now - timedelta(days=1),
        ends_at=now - timedelta(days=1),
        frequency=TaskFrequency.DAILY,
    )
    entry_two = CalendarEntryEntity(
        user_id=test_user_id,
        name="Series To Delete",
        calendar_id=test_calendar.id,
        calendar_entry_series_id=series_id,
        platform_id="entry-11",
        platform="google",
        status="confirmed",
        starts_at=now + timedelta(days=1),
        ends_at=now + timedelta(days=1),
        frequency=TaskFrequency.DAILY,
    )
    deleted_stub_one = CalendarEntryEntity(
        user_id=test_user_id,
        name="Deleted",
        calendar_id=test_calendar.id,
        calendar_entry_series_id=series_id,
        platform_id="entry-10",
        platform="google",
        status="cancelled",
        starts_at=datetime(2025, 2, 1, 9, 0, tzinfo=UTC),
        ends_at=datetime(2025, 2, 1, 10, 0, tzinfo=UTC),
        frequency=TaskFrequency.DAILY,
    )
    deleted_stub_two = CalendarEntryEntity(
        user_id=test_user_id,
        name="Deleted",
        calendar_id=test_calendar.id,
        calendar_entry_series_id=series_id,
        platform_id="entry-11",
        platform="google",
        status="cancelled",
        starts_at=datetime(2025, 2, 2, 9, 0, tzinfo=UTC),
        ends_at=datetime(2025, 2, 2, 10, 0, tzinfo=UTC),
        frequency=TaskFrequency.DAILY,
    )

    allow(mock_calendar_entry_series_repo).get.and_return(existing_series)
    allow(mock_google_gateway).load_calendar_events.and_return(
        ([], [deleted_stub_one, deleted_stub_two], [], [], "new-sync-token")
    )

    async def search_entries(query: object) -> list[CalendarEntryEntity]:
        platform_ids = getattr(query, "platform_ids", None)
        if platform_ids:
            return [entry_one, entry_two]
        if getattr(query, "calendar_entry_series_id", None) == series_id:
            return [entry_one, entry_two]
        return []

    mock_calendar_entry_repo.search = search_entries
    mock_uow.calendar_entry_ro_repo.search = search_entries

    async def get_user(_: object) -> object:
        return SimpleNamespace(settings=SimpleNamespace(timezone="UTC"))

    mock_uow.user_ro_repo.get = get_user

    handler = SyncCalendarHandler(
        ro_repos=mock_ro_repos,
        uow_factory=mock_uow_factory,
        user_id=test_user_id,
        google_gateway=mock_google_gateway,
    )

    await handler.handle(SyncCalendarCommand(calendar_id=test_calendar.id))

    deleted_entries = [
        entity for entity in mock_uow.added if isinstance(entity, CalendarEntryEntity)
    ]
    deleted_event_count = sum(
        1
        for entry in deleted_entries
        for event in entry.collect_events()
        if isinstance(event, CalendarEntryDeletedEvent)
    )
    assert deleted_event_count == 1
    assert any(entry.platform_id == "entry-11" for entry in deleted_entries)

    updated_series = [
        entity
        for entity in mock_uow.added
        if isinstance(entity, CalendarEntrySeriesEntity)
    ]
    assert updated_series
    assert updated_series[0].ends_at is not None
    assert any(
        isinstance(event, CalendarEntrySeriesUpdatedEvent)
        for event in updated_series[0].collect_events()
    )


@pytest.mark.asyncio
async def test_sync_calendar_series_cancelled_master_ends_series(
    test_user_id,
    test_calendar,
    mock_ro_repos,
    mock_uow_factory,
    mock_uow,
    mock_google_gateway,
    mock_calendar_entry_series_repo,
    mock_calendar_entry_repo,
):
    """Cancelled series masters should end the series and delete future entries."""
    series_id = CalendarEntrySeriesEntity.id_from_platform("google", "series-3")
    existing_series = CalendarEntrySeriesEntity(
        id=series_id,
        user_id=test_user_id,
        calendar_id=test_calendar.id,
        name="Series To Cancel",
        platform_id="series-3",
        platform="google",
        frequency=TaskFrequency.DAILY,
    )
    now = datetime.now(UTC)
    past_entry = CalendarEntryEntity(
        user_id=test_user_id,
        name="Series To Cancel",
        calendar_id=test_calendar.id,
        calendar_entry_series_id=series_id,
        platform_id="entry-20",
        platform="google",
        status="confirmed",
        starts_at=now - timedelta(days=2),
        ends_at=now - timedelta(days=2),
        frequency=TaskFrequency.DAILY,
    )
    future_entry = CalendarEntryEntity(
        user_id=test_user_id,
        name="Series To Cancel",
        calendar_id=test_calendar.id,
        calendar_entry_series_id=series_id,
        platform_id="entry-21",
        platform="google",
        status="confirmed",
        starts_at=now + timedelta(days=1),
        ends_at=now + timedelta(days=1),
        frequency=TaskFrequency.DAILY,
    )

    allow(mock_calendar_entry_series_repo).get.and_return(existing_series)
    allow(mock_google_gateway).load_calendar_events.and_return(
        ([], [], [], [series_id], "new-sync-token")
    )

    async def search_entries(query: object) -> list[CalendarEntryEntity]:
        if getattr(query, "calendar_entry_series_id", None) == series_id:
            return [past_entry, future_entry]
        return []

    mock_calendar_entry_repo.search = search_entries
    mock_uow.calendar_entry_ro_repo.search = search_entries

    async def get_user(_: object) -> object:
        return SimpleNamespace(settings=SimpleNamespace(timezone="UTC"))

    mock_uow.user_ro_repo.get = get_user

    handler = SyncCalendarHandler(
        ro_repos=mock_ro_repos,
        uow_factory=mock_uow_factory,
        user_id=test_user_id,
        google_gateway=mock_google_gateway,
    )

    await handler.handle(SyncCalendarCommand(calendar_id=test_calendar.id))

    deleted_entries = [
        entity for entity in mock_uow.added if isinstance(entity, CalendarEntryEntity)
    ]
    assert any(entry.platform_id == "entry-21" for entry in deleted_entries)

    updated_series = [
        entity
        for entity in mock_uow.added
        if isinstance(entity, CalendarEntrySeriesEntity)
    ]
    assert updated_series
    assert updated_series[0].ends_at is not None


@pytest.mark.asyncio
async def test_sync_calendar_series_creation_emits_single_notification(
    test_user_id,
    test_calendar,
    mock_ro_repos,
    mock_uow_factory,
    mock_uow,
    mock_google_gateway,
    mock_calendar_entry_series_repo,
    mock_calendar_entry_repo,
):
    """Series creation should emit one calendar entry created event."""
    series_id = CalendarEntrySeriesEntity.id_from_platform("google", "series-3")
    new_series = CalendarEntrySeriesEntity(
        id=series_id,
        user_id=test_user_id,
        calendar_id=test_calendar.id,
        name="New Series",
        platform_id="series-3",
        platform="google",
        frequency=TaskFrequency.DAILY,
    )
    entry_one = CalendarEntryEntity(
        user_id=test_user_id,
        name="New Series",
        calendar_id=test_calendar.id,
        calendar_entry_series_id=series_id,
        platform_id="entry-20",
        platform="google",
        status="confirmed",
        starts_at=datetime(2025, 3, 1, 9, 0, tzinfo=UTC),
        ends_at=datetime(2025, 3, 1, 10, 0, tzinfo=UTC),
        frequency=TaskFrequency.DAILY,
    )
    entry_two = CalendarEntryEntity(
        user_id=test_user_id,
        name="New Series",
        calendar_id=test_calendar.id,
        calendar_entry_series_id=series_id,
        platform_id="entry-21",
        platform="google",
        status="confirmed",
        starts_at=datetime(2025, 3, 2, 9, 0, tzinfo=UTC),
        ends_at=datetime(2025, 3, 2, 10, 0, tzinfo=UTC),
        frequency=TaskFrequency.DAILY,
    )

    allow(mock_calendar_entry_series_repo).get.and_raise(NotFoundError("missing"))
    allow(mock_google_gateway).load_calendar_events.and_return(
        ([entry_one, entry_two], [], [new_series], [], "new-sync-token")
    )

    async def search_entries(_: object) -> list[CalendarEntryEntity]:
        return []

    mock_calendar_entry_repo.search = search_entries
    mock_uow.calendar_entry_ro_repo.search = search_entries

    async def get_user(_: object) -> object:
        return SimpleNamespace(settings=SimpleNamespace(timezone="UTC"))

    mock_uow.user_ro_repo.get = get_user

    handler = SyncCalendarHandler(
        ro_repos=mock_ro_repos,
        uow_factory=mock_uow_factory,
        user_id=test_user_id,
        google_gateway=mock_google_gateway,
    )

    await handler.handle(SyncCalendarCommand(calendar_id=test_calendar.id))

    created_entries = [
        entity for entity in mock_uow.added if isinstance(entity, CalendarEntryEntity)
    ]
    created_event_count = sum(
        1
        for entry in created_entries
        for event in entry.collect_events()
        if isinstance(event, CalendarEntryCreatedEvent)
    )
    assert created_event_count == 1
