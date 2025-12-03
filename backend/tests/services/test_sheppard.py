import asyncio

import pytest
from dobles import expect

from planned.services import sheppard


@pytest.mark.asyncio
async def test_run(test_sheppard_svc):
    expect(sheppard.calendar_svc).sync_all().once()
    task = asyncio.create_task(test_sheppard_svc.run())
    await asyncio.sleep(0.1)

    test_sheppard_svc.stop()
    await task
