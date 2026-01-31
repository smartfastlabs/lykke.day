"""Unit tests for inbound SMS worker tasks."""

from uuid import uuid4

import pytest

from lykke.presentation.workers.tasks import inbound_sms as inbound_sms_tasks
from tests.unit.presentation.worker_task_helpers import (
    create_gateway_recorder,
    create_handler_recorder,
)


@pytest.mark.asyncio
async def test_process_inbound_sms_message_task_calls_handler() -> None:
    gateway, gateway_state = create_gateway_recorder()
    handler, handler_calls = create_handler_recorder()

    await inbound_sms_tasks.process_inbound_sms_message_task(
        user_id=uuid4(),
        message_id=uuid4(),
        handler=handler,
        pubsub_gateway=gateway,
    )

    assert handler_calls
    assert gateway_state["closed"] is True
