"""Unit tests for scheduling worker tasks."""

from datetime import date as dt_date
from uuid import uuid4

import pytest

from lykke.presentation.workers.tasks import scheduling as scheduling_tasks
from tests.unit.presentation.worker_task_helpers import (
    build_user,
    create_gateway_recorder,
    create_handler_recorder,
    create_task_recorder,
    create_user_repo,
)


@pytest.mark.asyncio
async def test_schedule_all_users_day_task_enqueues() -> None:
    users = [build_user(uuid4()), build_user(uuid4())]
    task, calls = create_task_recorder()
    user_repo = create_user_repo(users)

    await scheduling_tasks.schedule_all_users_day_task(
        user_repo=user_repo,
        enqueue_task=task,
    )

    assert len(calls) == 2


@pytest.mark.asyncio
async def test_schedule_user_day_task_handles_value_error() -> None:
    gateway, gateway_state = create_gateway_recorder()
    handler, _ = create_handler_recorder()

    async def raise_value_error(_: object) -> None:
        raise ValueError("missing template")

    handler.handle = raise_value_error

    await scheduling_tasks.schedule_user_day_task(
        user_id=uuid4(),
        user_repo=create_user_repo([build_user(uuid4())]),
        handler=handler,
        pubsub_gateway=gateway,
        current_date_provider=lambda _: dt_date(2025, 11, 27),
    )

    assert gateway_state["closed"] is True


@pytest.mark.asyncio
async def test_schedule_user_day_task_handles_generic_error() -> None:
    gateway, gateway_state = create_gateway_recorder()
    handler, _ = create_handler_recorder()

    async def raise_error(_: object) -> None:
        raise RuntimeError("boom")

    handler.handle = raise_error

    await scheduling_tasks.schedule_user_day_task(
        user_id=uuid4(),
        user_repo=create_user_repo([build_user(uuid4())]),
        handler=handler,
        pubsub_gateway=gateway,
        current_date_provider=lambda _: dt_date(2025, 11, 27),
    )

    assert gateway_state["closed"] is True
