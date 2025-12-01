import pytest

from planned.repositories import day_repo


@pytest.mark.asyncio
async def test_get(test_date):
    result = await day_repo.get(str(test_date))
    assert result.status == "SCHEDULED"
