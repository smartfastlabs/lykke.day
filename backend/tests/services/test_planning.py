import pytest

from planned.services import DayService, planning_svc


@pytest.mark.asyncio
async def test_schedule_today(test_date):
    result = await planning_svc.schedule(test_date)
    assert len(result.events) == 1

    assert result.events[0].name == "Sifleet Family Thanksgiving"

    assert len(result.tasks) == 2

    day_svc = await DayService.for_date(test_date)

    def sort_tasks(tasks):
        return sorted(tasks, key=lambda t: t.name)

    assert sort_tasks(day_svc.ctx.tasks) == sort_tasks(result.tasks)
    assert day_svc.ctx.day == result.day


@pytest.mark.asyncio
async def test_schedule_tomorrow(test_date_tomorrow):
    result = await planning_svc.schedule(test_date_tomorrow)

    assert result.day.template_id == "weekend"
    assert len(result.events) == 0
    assert len(result.tasks) == 2
