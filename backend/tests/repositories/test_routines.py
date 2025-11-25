import pytest

from planned.repositories import event_repo


@pytest.mark.asyncio
async def test_search(test_date):
    results = await event_repo.search(test_date)

    assert len(results) == 1
