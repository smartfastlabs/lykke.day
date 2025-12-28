import pytest

from planned.domain.entities import Day, DayStatus
from planned.infrastructure.repositories import DayRepository
from planned.infrastructure.utils.dates import get_current_datetime


@pytest.fixture
def day_repo(test_user):
    from uuid import UUID
    return DayRepository(user_uuid=UUID(test_user.id))


@pytest.mark.asyncio
async def test_get(test_date, test_user, day_repo):
    from uuid import UUID
    # Create a Day first
    day = Day(
        user_uuid=UUID(test_user.id),
        date=test_date,
        status=DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
    )
    await day_repo.put(day)

    # Now get it
    result = await day_repo.get(str(test_date))
    assert result.status == DayStatus.SCHEDULED
