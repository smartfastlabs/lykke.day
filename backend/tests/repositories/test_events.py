from datetime import timedelta

import pytest

from planned.repositories import event_repo


@pytest.mark.asyncio
async def test_search(test_date):
    results = await event_repo.search(test_date)

    assert len(results) == 1


@pytest.mark.asyncio
async def test_delete(test_date, clear_repos):
    results = await event_repo.search(test_date)
    await event_repo.delete(results[0])

    results = await event_repo.search(test_date)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_delete_missing_date(test_date, clear_repos):
    await event_repo.delete_by_date(test_date + timedelta(days=3))

    results = await event_repo.search(test_date)

    assert len(results) == 1


@pytest.mark.asyncio
async def test_delete_date(test_date, clear_repos):
    await event_repo.delete_by_date(test_date)

    results = await event_repo.search(test_date)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_delete_by_date(test_date, clear_repos):
    await event_repo.delete_by_date(test_date)

    results = await event_repo.search(test_date)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_put(clear_repos, test_event):
    await event_repo.put(
        test_event,
    )

    results = await event_repo.search(test_event.date)

    assert len(results) == 1
