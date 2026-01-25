"""Integration tests for Google Calendar sync with real database."""

from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio

from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntryEntity
from lykke.domain.value_objects import TaskFrequency
from lykke.infrastructure.gateways import GoogleCalendarGateway, StubPubSubGateway
from lykke.infrastructure.repositories import CalendarEntryRepository
from lykke.infrastructure.unit_of_work import (
    SqlAlchemyReadOnlyRepositoryFactory,
    SqlAlchemyUnitOfWorkFactory,
)


@pytest_asyncio.fixture
async def test_calendar(test_user, create_calendar):
    """Create a test calendar in the database."""
    return await create_calendar(
        user_id=test_user.id,
        name="Test Calendar",
        platform="google",
        platform_id="test@calendar.google.com",
    )


@pytest.fixture
def calendar_entry_repo(test_user):
    """Create a calendar entry repository."""
    return CalendarEntryRepository(user_id=test_user.id)


@pytest.mark.asyncio
async def test_sync_creates_new_events(test_user, test_calendar, calendar_entry_repo):
    """Test that sync creates new events in the database."""
    # Create a test event
    event = CalendarEntryEntity(
        user_id=test_user.id,
        calendar_id=test_calendar.id,
        platform_id="test-event-1",
        platform="google",
        status="confirmed",
        name="Test Meeting",
        starts_at=datetime.now(UTC) + timedelta(hours=1),
        ends_at=datetime.now(UTC) + timedelta(hours=2),
        frequency=TaskFrequency.ONCE,
    )

    # Save the event using repository
    uow_factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=StubPubSubGateway())
    uow = uow_factory.create(test_user.id)

    async with uow:
        event.create()
        uow.add(event)

    # Verify event was created
    retrieved = await calendar_entry_repo.search_one(
        value_objects.CalendarEntryQuery(platform_id="test-event-1")
    )
    assert retrieved.name == "Test Meeting"
    assert retrieved.platform_id == "test-event-1"

    # Cleanup
    async with uow:
        await uow.delete(event)


@pytest.mark.asyncio
async def test_sync_updates_existing_events(test_user, test_calendar, calendar_entry_repo):
    """Test that sync updates existing events in the database."""
    # Create initial event
    event = CalendarEntryEntity(
        user_id=test_user.id,
        calendar_id=test_calendar.id,
        platform_id="test-event-2",
        platform="google",
        status="confirmed",
        name="Original Name",
        starts_at=datetime.now(UTC) + timedelta(hours=1),
        ends_at=datetime.now(UTC) + timedelta(hours=2),
        frequency=TaskFrequency.ONCE,
    )

    uow_factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=StubPubSubGateway())
    uow = uow_factory.create(test_user.id)

    # Create initial event
    async with uow:
        event.create()
        uow.add(event)

    # Update the event
    updated_event = CalendarEntryEntity(
        id=event.id,  # Same ID for upsert
        user_id=test_user.id,
        calendar_id=test_calendar.id,
        platform_id="test-event-2",  # Same platform_id
        platform="google",
        status="confirmed",
        name="Updated Name",  # Changed name
        starts_at=datetime.now(UTC) + timedelta(hours=3),  # Changed time
        ends_at=datetime.now(UTC) + timedelta(hours=4),
        frequency=TaskFrequency.ONCE,
    )

    async with uow:
        updated_event.create()
        uow.add(updated_event)

    # Verify event was updated
    retrieved = await calendar_entry_repo.search_one(
        value_objects.CalendarEntryQuery(platform_id="test-event-2")
    )
    assert retrieved.name == "Updated Name"
    assert retrieved.platform_id == "test-event-2"

    # Cleanup
    async with uow:
        await uow.delete(updated_event)


@pytest.mark.asyncio
async def test_sync_deletes_cancelled_events(test_user, test_calendar, calendar_entry_repo):
    """Test that sync deletes cancelled events from the database."""
    # Create event
    event = CalendarEntryEntity(
        user_id=test_user.id,
        calendar_id=test_calendar.id,
        platform_id="test-event-3",
        platform="google",
        status="confirmed",
        name="Event to Delete",
        starts_at=datetime.now(UTC) + timedelta(hours=1),
        ends_at=datetime.now(UTC) + timedelta(hours=2),
        frequency=TaskFrequency.ONCE,
    )

    uow_factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=StubPubSubGateway())
    uow = uow_factory.create(test_user.id)

    # Create event
    async with uow:
        event.create()
        uow.add(event)

    # Verify event exists
    await calendar_entry_repo.search_one(
        value_objects.CalendarEntryQuery(platform_id="test-event-3")
    )

    # Delete the event
    async with uow:
        await uow.delete(event)

    # Verify event was deleted
    deleted = await calendar_entry_repo.search_one_or_none(
        value_objects.CalendarEntryQuery(platform_id="test-event-3")
    )
    assert deleted is None


@pytest.mark.asyncio
async def test_search_one_or_none_returns_none_for_nonexistent(
    test_user, calendar_entry_repo
):
    """Test that search_one_or_none returns None for nonexistent events."""
    result = await calendar_entry_repo.search_one_or_none(
        value_objects.CalendarEntryQuery(platform_id="nonexistent-event")
    )
    assert result is None


@pytest.mark.asyncio
async def test_upsert_with_same_platform_id(
    test_user, test_calendar, calendar_entry_repo
):
    """Test that upserting with the same platform_id updates the event."""
    # Create first version
    event1 = CalendarEntryEntity(
        user_id=test_user.id,
        calendar_id=test_calendar.id,
        platform_id="test-event-upsert",
        platform="google",
        status="confirmed",
        name="Version 1",
        starts_at=datetime.now(UTC) + timedelta(hours=1),
        ends_at=datetime.now(UTC) + timedelta(hours=2),
        frequency=TaskFrequency.ONCE,
    )

    uow_factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=StubPubSubGateway())
    uow = uow_factory.create(test_user.id)

    # Create first version
    async with uow:
        event1.create()
        uow.add(event1)

    # Get the ID that was generated
    retrieved1 = await calendar_entry_repo.search_one(
        value_objects.CalendarEntryQuery(platform_id="test-event-upsert")
    )
    assert retrieved1.name == "Version 1"
    original_id = retrieved1.id

    # Create second version with same platform_id but same ID (for upsert)
    event2 = CalendarEntryEntity(
        id=original_id,  # Use same ID for proper upsert
        user_id=test_user.id,
        calendar_id=test_calendar.id,
        platform_id="test-event-upsert",  # Same platform_id
        platform="google",
        status="confirmed",
        name="Version 2",  # Updated name
        starts_at=datetime.now(UTC) + timedelta(hours=3),
        ends_at=datetime.now(UTC) + timedelta(hours=4),
        frequency=TaskFrequency.ONCE,
    )

    async with uow:
        event2.create()
        uow.add(event2)

    # Verify it was updated, not duplicated
    retrieved2 = await calendar_entry_repo.search_one(
        value_objects.CalendarEntryQuery(platform_id="test-event-upsert")
    )
    assert retrieved2.name == "Version 2"
    assert retrieved2.id == original_id  # Same ID

    # Cleanup
    async with uow:
        await uow.delete(event2)
