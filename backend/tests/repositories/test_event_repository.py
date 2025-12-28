import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio

from planned import settings
from planned.domain import entities as objects
from planned.infrastructure.repositories import EventRepository
from planned.infrastructure.repositories.base import DateQuery


@pytest_asyncio.fixture
async def event_repo(test_date, test_user):
    from uuid import UUID

    repo = EventRepository(user_uuid=UUID(test_user.id))

    # Create event on test_date
    starts_at_today = datetime.datetime.combine(
        test_date,
        datetime.time(hour=2),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    )
    event_today = objects.Event(
        user_uuid=UUID(test_user.id),
        name="Test Event",
        frequency="ONCE",
        calendar_id="test-calendar",
        platform_id="test-id",
        platform="testing",
        status="status",
        starts_at=starts_at_today,
    )
    await repo.put(event_today)

    # Create event on test_date + 1 day
    test_date_next = test_date + timedelta(days=1)
    starts_at_next = datetime.datetime.combine(
        test_date_next,
        datetime.time(hour=2),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    )
    event_next = objects.Event(
        user_uuid=UUID(test_user.id),
        name="Test Event",
        frequency="ONCE",
        calendar_id="test-calendar-2",
        platform_id="test-id-2",
        platform="testing",
        status="status",
        starts_at=starts_at_next,
    )
    await repo.put(event_next)

    return repo


@pytest.mark.asyncio
async def test_search(test_date, event_repo):
    results = await event_repo.search_query(DateQuery(date=test_date))

    assert len(results) == 1


@pytest.mark.asyncio
async def test_delete(test_date, event_repo):
    results = await event_repo.search_query(DateQuery(date=test_date))
    await event_repo.delete(results[0])

    results = await event_repo.search_query(DateQuery(date=test_date))

    assert len(results) == 0


@pytest.mark.asyncio
async def test_delete_missing_date(test_date, event_repo):
    await event_repo.delete_many(DateQuery(date=test_date + timedelta(days=3)))

    results = await event_repo.search_query(DateQuery(date=test_date))

    assert len(results) == 1


@pytest.mark.asyncio
async def test_delete_date(test_date, event_repo):
    await event_repo.delete_many(DateQuery(date=test_date))

    results = await event_repo.search_query(DateQuery(date=test_date))

    assert len(results) == 0


@pytest.mark.asyncio
async def test_delete_by_date(test_date, event_repo):
    await event_repo.delete_many(DateQuery(date=test_date))

    results = await event_repo.search_query(DateQuery(date=test_date))

    assert len(results) == 0


@pytest.mark.asyncio
async def test_put(test_event, test_user, clear_repos):
    # clear_repos clears everything, so we need to ensure the user exists again
    from uuid import UUID

    from planned.infrastructure.repositories import UserRepository

    user_repo = UserRepository()
    # Re-create user after clear_repos (test_user fixture will be recreated, but we need to persist it)
    recreated_user = await user_repo.put(test_user)

    # Update test_event to use the recreated user's UUID
    test_event.user_uuid = UUID(recreated_user.id)

    # Create event_repo after user is recreated
    event_repo = EventRepository(user_uuid=UUID(recreated_user.id))

    results = await event_repo.search_query(DateQuery(date=test_event.date))

    assert len(results) == 0  # clear_repos cleared everything

    await event_repo.put(
        test_event,
    )

    results = await event_repo.search_query(DateQuery(date=test_event.date))

    assert len(results) == 1  # Now we have 1 event
