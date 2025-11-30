import asyncio

import pytest
from dobles import expect

from planned.services import sheppard, sheppard_svc


@pytest.mark.asyncio
async def test_schedule_today(test_date, clear_repos):
    result = await sheppard_svc.schedule_day(test_date)
    assert len(result.events) == 1

    assert result.events[0].name == "Sifleet Family Thanksgiving"

    assert len(result.tasks) == 2


@pytest.mark.asyncio
async def test_run():
    expect(sheppard.calendar_svc).sync_all().once()

    task = asyncio.create_task(sheppard_svc.run())
    await asyncio.sleep(0.1)

    sheppard_svc.stop()
    await task
