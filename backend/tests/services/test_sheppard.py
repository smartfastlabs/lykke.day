import asyncio

import pytest
from dobles import expect


@pytest.mark.asyncio
async def test_run(test_sheppard_svc):
    expect(test_sheppard_svc.calendar_service).sync_all().once()
    task = asyncio.create_task(test_sheppard_svc.run())
    await asyncio.sleep(0.1)

    test_sheppard_svc.stop()
    await task
