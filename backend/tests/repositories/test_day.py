import pytest

from planned.infrastructure.repositories import DayRepository


@pytest.fixture
def day_repo():
    return DayRepository()


@pytest.mark.asyncio
async def test_get(test_date, day_repo):
    result = await day_repo.get(str(test_date))
    assert result.status == "SCHEDULED"
