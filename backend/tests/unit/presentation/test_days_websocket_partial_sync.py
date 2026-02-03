"""Unit tests for DayContext partial sync WebSocket responses."""

from __future__ import annotations

import json
from datetime import date as dt_date
from uuid import uuid4

import pytest

from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, TaskEntity
from lykke.presentation.api.routers.days import _send_day_context_parts
from lykke.presentation.api.routers.dependencies.services import DayContextPartHandlers


class DummyWebSocket:
    """Simple WebSocket stub that records messages."""

    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []

    async def send_text(self, text: str) -> None:
        self.sent.append(json.loads(text))


class StaticHandler:
    """Handler stub that returns a pre-configured value."""

    def __init__(self, value: object) -> None:
        self._value = value

    async def handle(self, _query: object) -> object:
        return self._value


class FakeRoutinesHandler:
    async def handle(self, _query: object) -> list[object]:
        return []

    async def get_routines(
        self, _date_value: dt_date, *, tasks: list[TaskEntity] | None = None
    ) -> list[object]:
        _ = tasks
        return []


class FakeScheduleDayHandler:
    async def handle(self, _command: object) -> object:
        raise AssertionError(
            "ScheduleDayHandler should not be called for existing day."
        )


class FakePubSubGateway:
    async def get_latest_user_stream_entry(self, *, user_id: object, stream_type: str):
        return (
            "123-0",
            {
                "occurred_at": "2026-01-15T12:00:00Z",
                "user_id": str(user_id),
                "stream_type": stream_type,
            },
        )


@pytest.mark.asyncio
async def test_partial_sync_sends_part_payloads_in_order() -> None:
    user_id = uuid4()
    date_value = dt_date(2026, 1, 15)
    day = DayEntity(
        user_id=user_id, date=date_value, status=value_objects.DayStatus.STARTED
    )
    task = TaskEntity(
        user_id=user_id,
        scheduled_date=date_value,
        name="Test Task",
        status=value_objects.TaskStatus.NOT_STARTED,
        type=value_objects.TaskType.WORK,
        category=value_objects.TaskCategory.WORK,
        frequency=value_objects.TaskFrequency.ONCE,
    )

    part_handlers = DayContextPartHandlers(
        day=StaticHandler(day),
        tasks=StaticHandler([task]),
        calendar_entries=StaticHandler([]),
        routines=FakeRoutinesHandler(),
        brain_dumps=StaticHandler([]),
        push_notifications=StaticHandler([]),
        messages=StaticHandler([]),
    )
    websocket = DummyWebSocket()
    pubsub_gateway = FakePubSubGateway()

    last_id = await _send_day_context_parts(
        websocket=websocket,
        part_handlers=part_handlers,
        schedule_day_handler=FakeScheduleDayHandler(),
        pubsub_gateway=pubsub_gateway,
        user_id=user_id,
        date_value=date_value,
        user_timezone="UTC",
        parts=["day", "tasks"],
    )

    assert last_id == "123-0"
    assert len(websocket.sent) == 2

    first = websocket.sent[0]
    second = websocket.sent[1]

    assert first["type"] == "sync_response"
    assert first["partial_key"] == "day"
    assert first["sync_complete"] is False
    assert first["last_change_stream_id"] == "123-0"
    assert first["last_audit_log_timestamp"] == "2026-01-15T12:00:00Z"
    assert "day" in (first["partial_context"] or {})

    assert second["type"] == "sync_response"
    assert second["partial_key"] == "tasks"
    assert second["sync_complete"] is True
    assert second["last_change_stream_id"] == "123-0"
    assert second["last_audit_log_timestamp"] == "2026-01-15T12:00:00Z"
    assert len((second["partial_context"] or {}).get("tasks", [])) == 1
