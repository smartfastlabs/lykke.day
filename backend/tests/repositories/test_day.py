import pytest

from planned.domain.entities import Day, DayStatus
from planned.infrastructure.repositories import DayRepository
from planned.infrastructure.utils.dates import get_current_datetime


@pytest.fixture
def day_repo():
    return DayRepository()


@pytest.mark.asyncio
async def test_get(test_date, day_repo):
    # Create a Day first
    day = Day(
        date=test_date,
        status=DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
    )
    await day_repo.put(day)

    # Now get it
    result = await day_repo.get(str(test_date))
    assert result.status == DayStatus.SCHEDULED
