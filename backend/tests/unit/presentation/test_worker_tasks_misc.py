"""Unit tests for misc worker tasks."""

import pytest

from lykke.presentation.workers.tasks import misc as misc_tasks


@pytest.mark.asyncio
async def test_heartbeat_task() -> None:
    await misc_tasks.heartbeat_task()


@pytest.mark.asyncio
async def test_example_triggered_task() -> None:
    result = await misc_tasks.example_triggered_task("hello")

    assert result == {"status": "completed", "message": "hello"}
