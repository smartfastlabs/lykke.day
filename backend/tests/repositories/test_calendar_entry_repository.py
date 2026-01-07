import datetime
from datetime import UTC, timedelta
from uuid import NAMESPACE_DNS, uuid5
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio
from lykke.core.config import settings
from lykke.domain.entities import CalendarEntity, CalendarEntryEntity
from lykke.domain.value_objects.query import CalendarEntryQuery
from lykke.domain.value_objects.task import TaskFrequency
from lykke.infrastructure.repositories import CalendarEntryRepository, UserRepository


@pytest_asyncio.fixture
async def calendar_entry_repo(test_date, test_user):
    repo = CalendarEntryRepository(user_id=test_user.id)

    # Create calendar entry on test_date (convert to UTC)
    starts_at_today = datetime.datetime.combine(
        test_date,
        datetime.time(hour=2),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    calendar_entry_today = CalendarEntryEntity(
        user_id=test_user.id,
        name="Test Calendar Entry",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-id",
        platform="testing",
        status="status",
        starts_at=starts_at_today,
    )
    await repo.put(calendar_entry_today)

    # Create calendar entry on test_date + 1 day (convert to UTC)
    test_date_next = test_date + timedelta(days=1)
    starts_at_next = datetime.datetime.combine(
        test_date_next,
        datetime.time(hour=2),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    calendar_entry_next = CalendarEntryEntity(
        user_id=test_user.id,
        name="Test Calendar Entry",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar-2"),
        platform_id="test-id-2",
        platform="testing",
        status="status",
        starts_at=starts_at_next,
    )
    await repo.put(calendar_entry_next)

    return repo


@pytest.mark.asyncio
async def test_search(test_date, calendar_entry_repo):
    results = await calendar_entry_repo.search_query(
        CalendarEntryQuery(date=test_date)
    )

    assert len(results) == 1


@pytest.mark.asyncio
async def test_delete(test_date, calendar_entry_repo):
    results = await calendar_entry_repo.search_query(
        CalendarEntryQuery(date=test_date)
    )
    await calendar_entry_repo.delete(results[0])

    results = await calendar_entry_repo.search_query(
        CalendarEntryQuery(date=test_date)
    )

    assert len(results) == 0


@pytest.mark.asyncio
async def test_delete_missing_date(test_date, calendar_entry_repo):
    await calendar_entry_repo.delete_many(
        CalendarEntryQuery(date=test_date + timedelta(days=3))
    )

    results = await calendar_entry_repo.search_query(
        CalendarEntryQuery(date=test_date)
    )

    assert len(results) == 1


@pytest.mark.asyncio
async def test_delete_date(test_date, calendar_entry_repo):
    await calendar_entry_repo.delete_many(CalendarEntryQuery(date=test_date))

    results = await calendar_entry_repo.search_query(
        CalendarEntryQuery(date=test_date)
    )

    assert len(results) == 0


@pytest.mark.asyncio
async def test_delete_by_date(test_date, calendar_entry_repo):
    await calendar_entry_repo.delete_many(CalendarEntryQuery(date=test_date))

    results = await calendar_entry_repo.search_query(
        CalendarEntryQuery(date=test_date)
    )

    assert len(results) == 0


@pytest.mark.asyncio
async def test_put(test_calendar_entry, test_user, clear_repos):
    # clear_repos clears everything, so we need to ensure the user exists again
    user_repo = UserRepository()
    # Re-create user after clear_repos (test_user fixture will be recreated, but we need to persist it)
    recreated_user = await user_repo.put(test_user)

    # Update test_calendar_entry to use the recreated user's UUID
    test_calendar_entry.user_id = recreated_user.id

    # Create calendar_entry_repo after user is recreated
    calendar_entry_repo = CalendarEntryRepository(user_id=recreated_user.id)

    results = await calendar_entry_repo.search_query(
        CalendarEntryQuery(date=test_calendar_entry.date)
    )

    assert len(results) == 0  # clear_repos cleared everything

    await calendar_entry_repo.put(
        test_calendar_entry,
    )

    results = await calendar_entry_repo.search_query(
        CalendarEntryQuery(date=test_calendar_entry.date)
    )

    assert len(results) == 1  # Now we have 1 calendar entry

