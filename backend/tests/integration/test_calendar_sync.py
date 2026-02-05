"""Integration tests for Google Calendar sync with real database."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio

from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntryEntity
from lykke.domain.events.calendar_entry_events import CalendarEntryUpdatedEvent
from lykke.domain.value_objects import TaskFrequency
from lykke.domain.value_objects.update import CalendarEntryUpdateObject
from lykke.infrastructure.gateways import GoogleCalendarGateway, StubPubSubGateway
from lykke.infrastructure.repositories import CalendarEntryRepository
from lykke.infrastructure.repository_factories import SqlAlchemyReadOnlyRepositoryFactory
from lykke.infrastructure.unit_of_work import SqlAlchemyUnitOfWorkFactory


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
    return CalendarEntryRepository(user=test_user)


@pytest.mark.asyncio
async def test_sync_creates_new_events(test_user, test_calendar, calendar_entry_repo):
    """Test that sync creates new events in the database."""
    # Create a test event
    platform_id = f"test-event-{uuid4()}"
    event = CalendarEntryEntity(
        user_id=test_user.id,
        calendar_id=test_calendar.id,
        platform_id=platform_id,
        platform="google",
        status="confirmed",
        name="Test Meeting",
        starts_at=datetime.now(UTC) + timedelta(hours=1),
        ends_at=datetime.now(UTC) + timedelta(hours=2),
        frequency=TaskFrequency.ONCE,
    )

    # Save the event using repository
    uow_factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=StubPubSubGateway())
    uow = uow_factory.create(test_user)

    async with uow:
        event.create()
        uow.add(event)

    # Verify event was created
    retrieved = await calendar_entry_repo.search_one(
        value_objects.CalendarEntryQuery(platform_id=platform_id)
    )
    assert retrieved.name == "Test Meeting"
    assert retrieved.platform_id == platform_id

    # Cleanup
    async with uow:
        await uow.delete(event)


@pytest.mark.asyncio
async def test_sync_updates_existing_events(
    test_user, test_calendar, calendar_entry_repo
):
    """Test that sync updates existing events in the database."""
    # Create initial event
    platform_id = f"test-event-{uuid4()}"
    event = CalendarEntryEntity(
        user_id=test_user.id,
        calendar_id=test_calendar.id,
        platform_id=platform_id,
        platform="google",
        status="confirmed",
        name="Original Name",
        starts_at=datetime.now(UTC) + timedelta(hours=1),
        ends_at=datetime.now(UTC) + timedelta(hours=2),
        frequency=TaskFrequency.ONCE,
    )

    uow_factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=StubPubSubGateway())
    uow = uow_factory.create(test_user)

    # Create initial event
    async with uow:
        event.create()
        uow.add(event)

    # Update the event
    updated_event = CalendarEntryEntity(
        id=event.id,  # Same ID for upsert
        user_id=test_user.id,
        calendar_id=test_calendar.id,
        platform_id=platform_id,  # Same platform_id
        platform="google",
        status="confirmed",
        name="Updated Name",  # Changed name
        starts_at=datetime.now(UTC) + timedelta(hours=3),  # Changed time
        ends_at=datetime.now(UTC) + timedelta(hours=4),
        frequency=TaskFrequency.ONCE,
    )

    async with uow:
        updated_event.add_event(
            CalendarEntryUpdatedEvent(
                user_id=test_user.id,
                calendar_entry_id=updated_event.id,
                update_object=CalendarEntryUpdateObject(
                    name=updated_event.name,
                    starts_at=updated_event.starts_at,
                    ends_at=updated_event.ends_at,
                ),
            )
        )
        uow.add(updated_event)

    # Verify event was updated
    retrieved = await calendar_entry_repo.search_one(
        value_objects.CalendarEntryQuery(platform_id=platform_id)
    )
    assert retrieved.name == "Updated Name"
    assert retrieved.platform_id == platform_id

    # Cleanup
    async with uow:
        await uow.delete(updated_event)


@pytest.mark.asyncio
async def test_sync_deletes_cancelled_events(
    test_user, test_calendar, calendar_entry_repo
):
    """Test that sync deletes cancelled events from the database."""
    # Create event
    platform_id = f"test-event-{uuid4()}"
    event = CalendarEntryEntity(
        user_id=test_user.id,
        calendar_id=test_calendar.id,
        platform_id=platform_id,
        platform="google",
        status="confirmed",
        name="Event to Delete",
        starts_at=datetime.now(UTC) + timedelta(hours=1),
        ends_at=datetime.now(UTC) + timedelta(hours=2),
        frequency=TaskFrequency.ONCE,
    )

    uow_factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=StubPubSubGateway())
    uow = uow_factory.create(test_user)

    # Create event
    async with uow:
        event.create()
        uow.add(event)

    # Verify event exists
    await calendar_entry_repo.search_one(
        value_objects.CalendarEntryQuery(platform_id=platform_id)
    )

    # Delete the event
    async with uow:
        await uow.delete(event)

    # Verify event was deleted
    deleted = await calendar_entry_repo.search_one_or_none(
        value_objects.CalendarEntryQuery(platform_id=platform_id)
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
    platform_id = f"test-event-upsert-{uuid4()}"
    event1 = CalendarEntryEntity(
        user_id=test_user.id,
        calendar_id=test_calendar.id,
        platform_id=platform_id,
        platform="google",
        status="confirmed",
        name="Version 1",
        starts_at=datetime.now(UTC) + timedelta(hours=1),
        ends_at=datetime.now(UTC) + timedelta(hours=2),
        frequency=TaskFrequency.ONCE,
    )

    uow_factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=StubPubSubGateway())
    uow = uow_factory.create(test_user)

    # Create first version
    async with uow:
        event1.create()
        uow.add(event1)

    # Get the ID that was generated
    retrieved1 = await calendar_entry_repo.search_one(
        value_objects.CalendarEntryQuery(platform_id=platform_id)
    )
    assert retrieved1.name == "Version 1"
    original_id = retrieved1.id

    # Create second version with same platform_id but same ID (for upsert)
    event2 = CalendarEntryEntity(
        id=original_id,  # Use same ID for proper upsert
        user_id=test_user.id,
        calendar_id=test_calendar.id,
        platform_id=platform_id,  # Same platform_id
        platform="google",
        status="confirmed",
        name="Version 2",  # Updated name
        starts_at=datetime.now(UTC) + timedelta(hours=3),
        ends_at=datetime.now(UTC) + timedelta(hours=4),
        frequency=TaskFrequency.ONCE,
    )

    async with uow:
        event2.add_event(
            CalendarEntryUpdatedEvent(
                user_id=test_user.id,
                calendar_entry_id=event2.id,
                update_object=CalendarEntryUpdateObject(
                    name=event2.name,
                    starts_at=event2.starts_at,
                    ends_at=event2.ends_at,
                ),
            )
        )
        uow.add(event2)

    # Verify it was updated, not duplicated
    retrieved2 = await calendar_entry_repo.search_one(
        value_objects.CalendarEntryQuery(platform_id=platform_id)
    )
    assert retrieved2.name == "Version 2"
    assert retrieved2.id == original_id  # Same ID

    # Cleanup
    async with uow:
        await uow.delete(event2)
