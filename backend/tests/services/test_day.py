import pytest

from planned.services import day_svc


@pytest.mark.asyncio
async def test_schedule_today(test_date):
    result = await day_svc.schedule_day(test_date)
    assert len(result.events) == 1

    assert result.events[0].name == "Sifleet Family Thanksgiving"

    assert len(result.tasks) == 2

    assert await day_svc.load_day_context(test_date) == result
