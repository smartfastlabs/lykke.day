import asyncio
import contextlib
import json
from datetime import date
from uuid import UUID, uuid4

import pytest

from lykke.core.utils.domain_event_serialization import serialize_domain_event
from lykke.domain.events.day_events import ReminderAddedEvent
from lykke.domain.events.task_events import TaskCreatedEvent
from lykke.presentation.api.routers.days import _handle_realtime_events


class _FakeWebSocket:
    def __init__(self) -> None:
        self.messages: list[dict[str, object]] = []

    async def send_text(self, message: str) -> None:
        self.messages.append(json.loads(message))


class _FakeSubscription:
    def __init__(self, messages: list[dict[str, object]]) -> None:
        self._messages = list(messages)

    async def get_message(self, timeout: float) -> dict[str, object] | None:
        if self._messages:
            return self._messages.pop(0)
        await asyncio.sleep(timeout)
        return None


class _FakeIncrementalChangesHandler:
    async def _load_entity_data(
        self, entity_type: str, entity_id: UUID, *, user_timezone: str | None
    ) -> dict[str, object]:
        _ = user_timezone
        return {"id": str(entity_id), "entity_type": entity_type}


@pytest.mark.asyncio
async def test_realtime_task_created_event_is_forwarded() -> None:
    user_id = uuid4()
    task_id = uuid4()
    today = date(2026, 1, 25)
    event = TaskCreatedEvent(
        user_id=user_id,
        task_id=task_id,
        name="LLM Task",
        entity_id=task_id,
        entity_type="task",
        entity_date=today,
    )

    websocket = _FakeWebSocket()
    subscription = _FakeSubscription([serialize_domain_event(event)])
    handler = _FakeIncrementalChangesHandler()

    task = asyncio.create_task(
        _handle_realtime_events(websocket, subscription, today, handler, None)
    )
    await asyncio.sleep(0.05)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert websocket.messages
    response = websocket.messages[0]
    assert response["type"] == "sync_response"
    assert response["changes"]
    assert response["changes"][0]["entity_type"] == "task"
    assert response["changes"][0]["entity_id"] == str(task_id)


@pytest.mark.asyncio
async def test_realtime_reminder_added_event_is_forwarded() -> None:
    user_id = uuid4()
    day_id = uuid4()
    reminder_id = uuid4()
    today = date(2026, 1, 25)
    event = ReminderAddedEvent(
        user_id=user_id,
        day_id=day_id,
        date=today,
        reminder_id=reminder_id,
        reminder_name="LLM Reminder",
        entity_id=day_id,
        entity_type="day",
        entity_date=today,
    )

    websocket = _FakeWebSocket()
    subscription = _FakeSubscription([serialize_domain_event(event)])
    handler = _FakeIncrementalChangesHandler()

    task = asyncio.create_task(
        _handle_realtime_events(websocket, subscription, today, handler, None)
    )
    await asyncio.sleep(0.05)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert websocket.messages
    response = websocket.messages[0]
    assert response["type"] == "sync_response"
    assert response["changes"]
    assert response["changes"][0]["entity_type"] == "day"
    assert response["changes"][0]["entity_id"] == str(day_id)
