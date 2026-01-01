"""Integration tests for EventRepository."""

import datetime
from datetime import UTC
from uuid import UUID, uuid4, uuid5, NAMESPACE_DNS
from zoneinfo import ZoneInfo

import pytest

from planned.core.config import settings
from planned.core.exceptions import NotFoundError
from planned.domain.entities import Event
from planned.infrastructure.repositories import EventRepository
from planned.domain.value_objects.query import DateQuery


@pytest.mark.asyncio
async def test_get(event_repo, test_user, test_date):
    """Test getting an event by ID."""
    starts_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    event = Event(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Event",
        frequency="ONCE",
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id",
        platform="testing",
        status="confirmed",
        starts_at=starts_at,
    )
    await event_repo.put(event)
    
    result = await event_repo.get(event.id)
    
    assert result.id == event.id
    assert result.name == "Test Event"
    assert result.user_id == test_user.id


@pytest.mark.asyncio
async def test_get_not_found(event_repo):
    """Test getting a non-existent event raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await event_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put(event_repo, test_user, test_date):
    """Test creating a new event."""
    starts_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    event = Event(
        id=uuid4(),
        user_id=test_user.id,
        name="New Event",
        frequency="ONCE",
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id",
        platform="testing",
        status="confirmed",
        starts_at=starts_at,
    )
    
    result = await event_repo.put(event)
    
    assert result.name == "New Event"
    assert result.user_id == test_user.id
    assert result.date == test_date


@pytest.mark.asyncio
async def test_put_update(event_repo, test_user, test_date):
    """Test updating an existing event."""
    starts_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    event = Event(
        id=uuid4(),
        user_id=test_user.id,
        name="Original Event",
        frequency="ONCE",
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id",
        platform="testing",
        status="confirmed",
        starts_at=starts_at,
    )
    await event_repo.put(event)
    
    # Update the event
    event.name = "Updated Event"
    result = await event_repo.put(event)
    
    assert result.name == "Updated Event"
    
    # Verify it was saved
    retrieved = await event_repo.get(event.id)
    assert retrieved.name == "Updated Event"


@pytest.mark.asyncio
async def test_all(event_repo, test_user, test_date, test_date_tomorrow):
    """Test getting all events."""
    starts_at1 = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    starts_at2 = datetime.datetime.combine(
        test_date_tomorrow,
        datetime.time(hour=14),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    
    event1 = Event(
        id=uuid4(),
        user_id=test_user.id,
        name="Event 1",
        frequency="ONCE",
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id-1",
        platform="testing",
        status="confirmed",
        starts_at=starts_at1,
    )
    event2 = Event(
        id=uuid4(),
        user_id=test_user.id,
        name="Event 2",
        frequency="ONCE",
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id-2",
        platform="testing",
        status="confirmed",
        starts_at=starts_at2,
    )
    await event_repo.put(event1)
    await event_repo.put(event2)
    
    all_events = await event_repo.all()
    
    event_ids = [e.id for e in all_events]
    assert event1.id in event_ids
    assert event2.id in event_ids


@pytest.mark.asyncio
async def test_search_query(event_repo, test_user, test_date, test_date_tomorrow):
    """Test searching events with DateQuery."""
    starts_at1 = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    starts_at2 = datetime.datetime.combine(
        test_date_tomorrow,
        datetime.time(hour=14),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    
    event1 = Event(
        id=uuid4(),
        user_id=test_user.id,
        name="Event Today",
        frequency="ONCE",
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id-1",
        platform="testing",
        status="confirmed",
        starts_at=starts_at1,
    )
    event2 = Event(
        id=uuid4(),
        user_id=test_user.id,
        name="Event Tomorrow",
        frequency="ONCE",
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id-2",
        platform="testing",
        status="confirmed",
        starts_at=starts_at2,
    )
    await event_repo.put(event1)
    await event_repo.put(event2)
    
    # Search for specific date
    results = await event_repo.search_query(DateQuery(date=test_date))
    
    assert len(results) == 1
    assert results[0].date == test_date
    assert results[0].name == "Event Today"


@pytest.mark.asyncio
async def test_delete(event_repo, test_user, test_date):
    """Test deleting an event."""
    starts_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    event = Event(
        id=uuid4(),
        user_id=test_user.id,
        name="Event to Delete",
        frequency="ONCE",
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id",
        platform="testing",
        status="confirmed",
        starts_at=starts_at,
    )
    await event_repo.put(event)
    
    # Delete it
    await event_repo.delete(event)
    
    # Should not be found
    with pytest.raises(NotFoundError):
        await event_repo.get(event.id)


@pytest.mark.asyncio
async def test_delete_many(event_repo, test_user, test_date, test_date_tomorrow):
    """Test deleting multiple events by date."""
    starts_at1 = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    starts_at2 = datetime.datetime.combine(
        test_date,
        datetime.time(hour=14),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    starts_at3 = datetime.datetime.combine(
        test_date_tomorrow,
        datetime.time(hour=16),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    
    event1 = Event(
        id=uuid4(),
        user_id=test_user.id,
        name="Event 1",
        frequency="ONCE",
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id-1",
        platform="testing",
        status="confirmed",
        starts_at=starts_at1,
    )
    event2 = Event(
        id=uuid4(),
        user_id=test_user.id,
        name="Event 2",
        frequency="ONCE",
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id-2",
        platform="testing",
        status="confirmed",
        starts_at=starts_at2,
    )
    event3 = Event(
        id=uuid4(),
        user_id=test_user.id,
        name="Event 3",
        frequency="ONCE",
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id-3",
        platform="testing",
        status="confirmed",
        starts_at=starts_at3,
    )
    await event_repo.put(event1)
    await event_repo.put(event2)
    await event_repo.put(event3)
    
    # Delete all events for test_date
    await event_repo.delete_many(DateQuery(date=test_date))
    
    # Events on test_date should be gone
    results = await event_repo.search_query(DateQuery(date=test_date))
    assert len(results) == 0
    
    # Event on test_date_tomorrow should still exist
    results_tomorrow = await event_repo.search_query(DateQuery(date=test_date_tomorrow))
    assert len(results_tomorrow) == 1
    assert results_tomorrow[0].name == "Event 3"


@pytest.mark.asyncio
async def test_user_isolation(event_repo, test_user, create_test_user, test_date):
    """Test that different users' events are properly isolated."""
    starts_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    
    # Create event for test_user
    event = Event(
        id=uuid4(),
        user_id=test_user.id,
        name="User1 Event",
        frequency="ONCE",
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id",
        platform="testing",
        status="confirmed",
        starts_at=starts_at,
    )
    await event_repo.put(event)
    
    # Create another user
    user2 = await create_test_user()
    event_repo2 = EventRepository(user_id=user2.id)
    
    # User2 should not see user1's event
    with pytest.raises(NotFoundError):
        await event_repo2.get(event.id)
    
    # User1 should still see their event
    result = await event_repo.get(event.id)
    assert result.user_id == test_user.id

