import asyncio

import pytest
from dobles import expect

from planned.services import sheppard, sheppard_svc


@pytest.mark.asyncio
async def test_run():
    expect(sheppard.calendar_svc).sync_all().once()

    task = asyncio.create_task(sheppard_svc.run())
    await asyncio.sleep(0.1)

    sheppard_svc.stop()
    await task
