from datetime import timedelta

import pytest

from planned.infrastructure.repositories import EventRepository


@pytest.fixture
def event_repo():
    return EventRepository()


@pytest.mark.asyncio
async def test_search(test_date, event_repo):
    results = await event_repo.search(test_date)

    assert len(results) == 1


@pytest.mark.asyncio
async def test_delete(test_date, event_repo):
    results = await event_repo.search(test_date)
    await event_repo.delete(results[0])

    results = await event_repo.search(test_date)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_delete_missing_date(test_date, event_repo):
    await event_repo.delete_by_date(test_date + timedelta(days=3))

    results = await event_repo.search(test_date)

    assert len(results) == 1


@pytest.mark.asyncio
async def test_delete_date(test_date, event_repo):
    await event_repo.delete_by_date(test_date)

    results = await event_repo.search(test_date)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_delete_by_date(test_date, event_repo):
    await event_repo.delete_by_date(test_date)

    results = await event_repo.search(test_date)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_put(test_event, clear_repos, event_repo):
    await event_repo.put(
        test_event,
    )

    results = await event_repo.search(test_event.date)

    assert len(results) == 1
