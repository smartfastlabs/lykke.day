"""Unit tests for scheduling worker tasks."""

from datetime import date as dt_date
from datetime import time as dt_time
from uuid import uuid4

import pytest

from lykke.presentation.workers.tasks import scheduling as scheduling_tasks
from tests.unit.presentation.worker_task_helpers import (
    build_user,
    create_identity_access,
    create_gateway_recorder,
    create_handler_recorder,
    create_task_recorder,
)


@pytest.mark.asyncio
async def test_schedule_all_users_day_task_enqueues() -> None:
    users = [build_user(uuid4()), build_user(uuid4())]
    task, calls = create_task_recorder()
    identity_access = create_identity_access(users)

    await scheduling_tasks.schedule_all_users_day_task(
        identity_access=identity_access,
        enqueue_task=task,
        current_time_provider=lambda _: dt_time(3, 5),
        delay_seconds_provider=lambda: 90,
    )

    assert len(calls) == 2
    assert calls[0]["delay_seconds"] == 90
    assert calls[1]["delay_seconds"] == 90


@pytest.mark.asyncio
async def test_schedule_all_users_day_task_skips_when_not_local_305() -> None:
    users = [build_user(uuid4()), build_user(uuid4())]
    task, calls = create_task_recorder()
    identity_access = create_identity_access(users)

    await scheduling_tasks.schedule_all_users_day_task(
        identity_access=identity_access,
        enqueue_task=task,
        current_time_provider=lambda _: dt_time(2, 59),
    )

    assert len(calls) == 0


@pytest.mark.asyncio
async def test_schedule_all_users_day_task_respects_user_timezone_local_time() -> None:
    utc_user = build_user(uuid4(), timezone="UTC")
    ist_user = build_user(uuid4(), timezone="Asia/Kolkata")
    users = [utc_user, ist_user]
    task, calls = create_task_recorder()
    identity_access = create_identity_access(users)

    def current_time_provider(timezone: str | None) -> dt_time:
        if timezone == "Asia/Kolkata":
            return dt_time(3, 5)
        return dt_time(2, 35)

    await scheduling_tasks.schedule_all_users_day_task(
        identity_access=identity_access,
        enqueue_task=task,
        current_time_provider=current_time_provider,
        delay_seconds_provider=lambda: 75,
    )

    assert len(calls) == 1
    assert calls[0]["user_id"] == ist_user.id
    assert calls[0]["delay_seconds"] == 75


@pytest.mark.asyncio
async def test_schedule_user_day_task_handles_value_error() -> None:
    gateway, gateway_state = create_gateway_recorder()
    handler, _ = create_handler_recorder()

    async def raise_value_error(_: object) -> None:
        raise ValueError("missing template")

    handler.handle = raise_value_error

    await scheduling_tasks.schedule_user_day_task(
        user_id=uuid4(),
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
        handler=handler,
        pubsub_gateway=gateway,
        current_date_provider=lambda _: dt_date(2025, 11, 27),
    )

    assert gateway_state["closed"] is True
