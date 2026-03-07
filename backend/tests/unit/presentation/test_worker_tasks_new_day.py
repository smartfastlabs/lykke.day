"""Unit tests for new-day event worker tasks."""

from datetime import date as dt_date
from datetime import time as dt_time
from uuid import uuid4

import pytest

from lykke.presentation.workers.tasks import new_day as new_day_tasks
from tests.unit.presentation.worker_task_helpers import (
    build_user,
    create_identity_access,
    create_gateway_recorder,
    create_task_recorder,
)


@pytest.mark.asyncio
async def test_emit_new_day_event_for_all_users_task_enqueues() -> None:
    users = [build_user(uuid4()), build_user(uuid4())]
    task, calls = create_task_recorder()
    identity_access = create_identity_access(users)

    await new_day_tasks.emit_new_day_event_for_all_users_task(
        identity_access=identity_access,
        enqueue_task=task,
        current_time_provider=lambda _: dt_time(3, 5),
        delay_seconds_provider=lambda: 120,
    )

    assert len(calls) == 2
    assert calls[0]["delay_seconds"] == 120
    assert calls[1]["delay_seconds"] == 120


@pytest.mark.asyncio
async def test_emit_new_day_event_for_all_users_task_skips_when_not_local_305() -> None:
    users = [build_user(uuid4()), build_user(uuid4())]
    task, calls = create_task_recorder()
    identity_access = create_identity_access(users)

    await new_day_tasks.emit_new_day_event_for_all_users_task(
        identity_access=identity_access,
        enqueue_task=task,
        current_time_provider=lambda _: dt_time(3, 4),
    )

    assert len(calls) == 0


@pytest.mark.asyncio
async def test_emit_new_day_event_for_all_users_task_respects_user_timezone_local_time() -> None:
    utc_user = build_user(uuid4(), timezone="UTC")
    ist_user = build_user(uuid4(), timezone="Asia/Kolkata")
    users = [utc_user, ist_user]
    task, calls = create_task_recorder()
    identity_access = create_identity_access(users)

    def current_time_provider(timezone: str | None) -> dt_time:
        if timezone == "Asia/Kolkata":
            return dt_time(3, 5)
        return dt_time(2, 35)

    await new_day_tasks.emit_new_day_event_for_all_users_task(
        identity_access=identity_access,
        enqueue_task=task,
        current_time_provider=current_time_provider,
        delay_seconds_provider=lambda: 105,
    )

    assert len(calls) == 1
    assert calls[0]["user_id"] == ist_user.id
    assert calls[0]["delay_seconds"] == 105


@pytest.mark.asyncio
async def test_emit_new_day_event_for_user_task_publishes_and_closes_gateway() -> None:
    user_id = uuid4()
    identity_access = create_identity_access([build_user(user_id)])
    gateway, gateway_state = create_gateway_recorder()

    published: list[dict[str, object]] = []

    async def publish_to_user_channel(**kwargs: object) -> None:
        published.append(kwargs)

    gateway.publish_to_user_channel = publish_to_user_channel

    await new_day_tasks.emit_new_day_event_for_user_task(
        user_id=user_id,
        identity_access=identity_access,
        pubsub_gateway=gateway,
        current_date_provider=lambda _: dt_date(2025, 11, 27),
    )

    assert gateway_state["closed"] is True
    assert len(published) == 1
    assert published[0]["user_id"] == user_id
    assert published[0]["channel_type"] == "domain-events"

    message = published[0]["message"]
    assert isinstance(message, dict)
    assert message["event_type"].endswith(".NewDayEvent")
    assert message["event_data"]["user_id"] == str(user_id)
    assert message["event_data"]["date"] == "2025-11-27"


@pytest.mark.asyncio
async def test_emit_new_day_event_for_user_task_handles_missing_user() -> None:
    # If user lookup fails, we still publish using UTC "today" and close the gateway.
    user_id = uuid4()
    identity_access = create_identity_access([])
    gateway, gateway_state = create_gateway_recorder()

    published: list[dict[str, object]] = []

    async def publish_to_user_channel(**kwargs: object) -> None:
        published.append(kwargs)

    gateway.publish_to_user_channel = publish_to_user_channel

    await new_day_tasks.emit_new_day_event_for_user_task(
        user_id=user_id,
        identity_access=identity_access,
        pubsub_gateway=gateway,
        current_date_provider=lambda _: dt_date(2025, 11, 27),
    )

    assert gateway_state["closed"] is True
    assert len(published) == 1
