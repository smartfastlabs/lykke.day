"""Integration tests for CalendarEntryRepository."""

import datetime
from datetime import UTC
from uuid import UUID, uuid4, uuid5, NAMESPACE_DNS
from zoneinfo import ZoneInfo

import pytest

from planned.core.config import settings
from planned.core.exceptions import NotFoundError
from planned.domain.entities import CalendarEntry
from planned.domain.value_objects.task import TaskFrequency
from planned.infrastructure.repositories import CalendarEntryRepository
from planned.domain.value_objects.query import DateQuery


@pytest.mark.asyncio
async def test_get(calendar_entry_repo, test_user, test_date):
    """Test getting a calendar entry by ID."""
    starts_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    calendar_entry = CalendarEntry(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Calendar Entry",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id",
        platform="testing",
        status="confirmed",
        starts_at=starts_at,
    )
    await calendar_entry_repo.put(calendar_entry)
    
    result = await calendar_entry_repo.get(calendar_entry.id)
    
    assert result.id == calendar_entry.id
    assert result.name == "Test Calendar Entry"
    assert result.user_id == test_user.id


@pytest.mark.asyncio
async def test_get_not_found(calendar_entry_repo):
    """Test getting a non-existent calendar entry raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await calendar_entry_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put(calendar_entry_repo, test_user, test_date):
    """Test creating a new calendar entry."""
    starts_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    calendar_entry = CalendarEntry(
        id=uuid4(),
        user_id=test_user.id,
        name="New Calendar Entry",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id",
        platform="testing",
        status="confirmed",
        starts_at=starts_at,
    )
    
    result = await calendar_entry_repo.put(calendar_entry)
    
    assert result.name == "New Calendar Entry"
    assert result.user_id == test_user.id
    assert result.date == test_date


@pytest.mark.asyncio
async def test_put_update(calendar_entry_repo, test_user, test_date):
    """Test updating an existing calendar entry."""
    starts_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    calendar_entry = CalendarEntry(
        id=uuid4(),
        user_id=test_user.id,
        name="Original Calendar Entry",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id",
        platform="testing",
        status="confirmed",
        starts_at=starts_at,
    )
    await calendar_entry_repo.put(calendar_entry)
    
    # Update the calendar entry
    calendar_entry.name = "Updated Calendar Entry"
    result = await calendar_entry_repo.put(calendar_entry)
    
    assert result.name == "Updated Calendar Entry"
    
    # Verify it was saved
    retrieved = await calendar_entry_repo.get(calendar_entry.id)
    assert retrieved.name == "Updated Calendar Entry"


@pytest.mark.asyncio
async def test_all(calendar_entry_repo, test_user, test_date, test_date_tomorrow):
    """Test getting all calendar entries."""
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
    
    calendar_entry1 = CalendarEntry(
        id=uuid4(),
        user_id=test_user.id,
        name="Calendar Entry 1",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id-1",
        platform="testing",
        status="confirmed",
        starts_at=starts_at1,
    )
    calendar_entry2 = CalendarEntry(
        id=uuid4(),
        user_id=test_user.id,
        name="Calendar Entry 2",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id-2",
        platform="testing",
        status="confirmed",
        starts_at=starts_at2,
    )
    await calendar_entry_repo.put(calendar_entry1)
    await calendar_entry_repo.put(calendar_entry2)
    
    all_calendar_entries = await calendar_entry_repo.all()
    
    calendar_entry_ids = [e.id for e in all_calendar_entries]
    assert calendar_entry1.id in calendar_entry_ids
    assert calendar_entry2.id in calendar_entry_ids


@pytest.mark.asyncio
async def test_search_query(calendar_entry_repo, test_user, test_date, test_date_tomorrow):
    """Test searching calendar entries with DateQuery."""
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
    
    calendar_entry1 = CalendarEntry(
        id=uuid4(),
        user_id=test_user.id,
        name="Calendar Entry Today",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id-1",
        platform="testing",
        status="confirmed",
        starts_at=starts_at1,
    )
    calendar_entry2 = CalendarEntry(
        id=uuid4(),
        user_id=test_user.id,
        name="Calendar Entry Tomorrow",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id-2",
        platform="testing",
        status="confirmed",
        starts_at=starts_at2,
    )
    await calendar_entry_repo.put(calendar_entry1)
    await calendar_entry_repo.put(calendar_entry2)
    
    # Search for specific date
    results = await calendar_entry_repo.search_query(DateQuery(date=test_date))
    
    assert len(results) == 1
    assert results[0].date == test_date
    assert results[0].name == "Calendar Entry Today"


@pytest.mark.asyncio
async def test_delete(calendar_entry_repo, test_user, test_date):
    """Test deleting a calendar entry."""
    starts_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    calendar_entry = CalendarEntry(
        id=uuid4(),
        user_id=test_user.id,
        name="Calendar Entry to Delete",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id",
        platform="testing",
        status="confirmed",
        starts_at=starts_at,
    )
    await calendar_entry_repo.put(calendar_entry)
    
    # Delete it
    await calendar_entry_repo.delete(calendar_entry)
    
    # Should not be found
    with pytest.raises(NotFoundError):
        await calendar_entry_repo.get(calendar_entry.id)


@pytest.mark.asyncio
async def test_delete_many(calendar_entry_repo, test_user, test_date, test_date_tomorrow):
    """Test deleting multiple calendar entries by date."""
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
    
    calendar_entry1 = CalendarEntry(
        id=uuid4(),
        user_id=test_user.id,
        name="Calendar Entry 1",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id-1",
        platform="testing",
        status="confirmed",
        starts_at=starts_at1,
    )
    calendar_entry2 = CalendarEntry(
        id=uuid4(),
        user_id=test_user.id,
        name="Calendar Entry 2",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id-2",
        platform="testing",
        status="confirmed",
        starts_at=starts_at2,
    )
    calendar_entry3 = CalendarEntry(
        id=uuid4(),
        user_id=test_user.id,
        name="Calendar Entry 3",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id-3",
        platform="testing",
        status="confirmed",
        starts_at=starts_at3,
    )
    await calendar_entry_repo.put(calendar_entry1)
    await calendar_entry_repo.put(calendar_entry2)
    await calendar_entry_repo.put(calendar_entry3)
    
    # Delete all calendar entries for test_date
    await calendar_entry_repo.delete_many(DateQuery(date=test_date))
    
    # Calendar entries on test_date should be gone
    results = await calendar_entry_repo.search_query(DateQuery(date=test_date))
    assert len(results) == 0
    
    # Calendar entry on test_date_tomorrow should still exist
    results_tomorrow = await calendar_entry_repo.search_query(DateQuery(date=test_date_tomorrow))
    assert len(results_tomorrow) == 1
    assert results_tomorrow[0].name == "Calendar Entry 3"


@pytest.mark.asyncio
async def test_user_isolation(calendar_entry_repo, test_user, create_test_user, test_date):
    """Test that different users' calendar entries are properly isolated."""
    starts_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    
    # Create calendar entry for test_user
    calendar_entry = CalendarEntry(
        id=uuid4(),
        user_id=test_user.id,
        name="User1 Calendar Entry",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id",
        platform="testing",
        status="confirmed",
        starts_at=starts_at,
    )
    await calendar_entry_repo.put(calendar_entry)
    
    # Create another user
    user2 = await create_test_user()
    calendar_entry_repo2 = CalendarEntryRepository(user_id=user2.id)
    
    # User2 should not see user1's calendar entry
    with pytest.raises(NotFoundError):
        await calendar_entry_repo2.get(calendar_entry.id)
    
    # User1 should still see their calendar entry
    result = await calendar_entry_repo.get(calendar_entry.id)
    assert result.user_id == test_user.id

