import pytest

from planned.services import planning_svc


@pytest.mark.asyncio
async def test_schedule_today(test_date):
    result = await planning_svc.schedule_day(test_date)
    assert len(result.events) == 1

    assert result.events[0].name == "Sifleet Family Thanksgiving"


    assert len(result.routine_instances) == 2