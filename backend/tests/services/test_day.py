import pytest
from freezegun import freeze_time

from planned import objects
from planned.application.services import DayService


@pytest.mark.asyncio
async def test_get_upcomming_events(test_day_svc, test_event_today):
    assert await test_day_svc.get_upcomming_events() == []
    with freeze_time(
        "2025-11-27 01:45:00-6:00",
        real_asyncio=True,
    ):
        assert await test_day_svc.get_upcomming_events() == [test_event_today]


@pytest.mark.asyncio
async def test_get_upcomming_tasks(test_day_svc, test_task_today):
    assert await test_day_svc.get_upcomming_tasks() == []
    with freeze_time(
        "2025-11-27 01:45:00-6:00",
        real_asyncio=True,
    ):
        assert await test_day_svc.get_upcomming_tasks() == [test_task_today]
