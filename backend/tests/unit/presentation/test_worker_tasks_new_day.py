"""Unit tests for new-day event worker tasks."""

from datetime import date as dt_date
from uuid import uuid4

import pytest
from dobles import allow

from lykke.presentation.workers.tasks import new_day as new_day_tasks
from tests.unit.presentation.worker_task_helpers import (
    build_user,
    create_gateway_recorder,
    create_task_recorder,
    create_user_repo,
)


@pytest.mark.asyncio
async def test_emit_new_day_event_for_all_users_task_enqueues() -> None:
    users = [build_user(uuid4()), build_user(uuid4())]
    task, calls = create_task_recorder()
    user_repo = create_user_repo(users)

    await new_day_tasks.emit_new_day_event_for_all_users_task(
        user_repo=user_repo,
        enqueue_task=task,
    )

    assert len(calls) == 2


@pytest.mark.asyncio
async def test_emit_new_day_event_for_user_task_publishes_and_closes_gateway() -> None:
    user_id = uuid4()
    user_repo = create_user_repo([build_user(user_id)])
    gateway, gateway_state = create_gateway_recorder()

    published: list[dict[str, object]] = []

    async def publish_to_user_channel(**kwargs: object) -> None:
        published.append(kwargs)

    gateway.publish_to_user_channel = publish_to_user_channel

    await new_day_tasks.emit_new_day_event_for_user_task(
        user_id=user_id,
        user_repo=user_repo,
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
    user_repo = create_user_repo([build_user(user_id)])
    allow(user_repo).get.and_raise(RuntimeError("boom"))
    gateway, gateway_state = create_gateway_recorder()

    published: list[dict[str, object]] = []

    async def publish_to_user_channel(**kwargs: object) -> None:
        published.append(kwargs)

    gateway.publish_to_user_channel = publish_to_user_channel

    await new_day_tasks.emit_new_day_event_for_user_task(
        user_id=user_id,
        user_repo=user_repo,
        pubsub_gateway=gateway,
        current_date_provider=lambda _: dt_date(2025, 11, 27),
    )

    assert gateway_state["closed"] is True
    assert len(published) == 1
