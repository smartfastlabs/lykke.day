"""Unit tests for timing-status worker tasks."""

from uuid import uuid4

import pytest

from lykke.application.commands.timing_status import EvaluateTimingStatusCommand
from lykke.presentation.workers.tasks import timing_status as timing_status_tasks
from tests.unit.presentation.worker_task_helpers import (
    build_user,
    create_gateway_recorder,
    create_handler_recorder,
    create_identity_access,
    create_task_recorder,
)


@pytest.mark.asyncio
async def test_evaluate_timing_status_for_all_users_task_enqueues() -> None:
    users = [build_user(uuid4()), build_user(uuid4())]
    task, calls = create_task_recorder()
    identity_access = create_identity_access(users)

    await timing_status_tasks.evaluate_timing_status_for_all_users_task(
        identity_access=identity_access,
        enqueue_task=task,
    )

    assert len(calls) == 2


@pytest.mark.asyncio
async def test_evaluate_timing_status_for_user_task_calls_handler() -> None:
    gateway, gateway_state = create_gateway_recorder()
    handler, handler_calls = create_handler_recorder()

    await timing_status_tasks.evaluate_timing_status_for_user_task(
        user_id=uuid4(),
        handler=handler,
        pubsub_gateway=gateway,
    )

    assert len(handler_calls) == 1
    assert isinstance(handler_calls[0], EvaluateTimingStatusCommand)
    assert gateway_state["closed"] is True


@pytest.mark.asyncio
async def test_evaluate_timing_status_for_user_task_handles_missing_user() -> None:
    user_id = uuid4()
    gateway, gateway_state = create_gateway_recorder()

    await timing_status_tasks.evaluate_timing_status_for_user_task(
        user_id=user_id,
        pubsub_gateway=gateway,
    )

    assert gateway_state["closed"] is True
