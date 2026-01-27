"""Unit tests for brain dump worker tasks."""

from uuid import uuid4

import pytest

from lykke.presentation.workers.tasks import brain_dump as brain_dump_tasks
from tests.unit.presentation.worker_task_helpers import (
    create_gateway_recorder,
    create_handler_recorder,
)


@pytest.mark.asyncio
async def test_process_brain_dump_item_task_handles_invalid_date() -> None:
    await brain_dump_tasks.process_brain_dump_item_task(
        user_id=uuid4(), day_date="bad", item_id=uuid4()
    )


@pytest.mark.asyncio
async def test_process_brain_dump_item_task_calls_handler() -> None:
    gateway, gateway_state = create_gateway_recorder()
    handler, handler_calls = create_handler_recorder()

    await brain_dump_tasks.process_brain_dump_item_task(
        user_id=uuid4(),
        day_date="2025-11-27",
        item_id=uuid4(),
        handler=handler,
        pubsub_gateway=gateway,
    )

    assert handler_calls
    assert gateway_state["closed"] is True
