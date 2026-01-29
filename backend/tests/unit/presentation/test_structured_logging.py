"""Unit tests for structured logging helpers."""

from __future__ import annotations

import pytest

from lykke.presentation.utils import structured_logging


class _FakeGateway:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.closed = False

    async def log_event(
        self,
        *,
        event_type: str,
        event_data: dict[str, object],
        occurred_at,
    ) -> None:
        self.calls.append(
            {
                "event_type": event_type,
                "event_data": event_data,
                "occurred_at": occurred_at,
            }
        )

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_emit_structured_log_uses_gateway(monkeypatch) -> None:
    gateway = _FakeGateway()

    def _gateway_factory() -> _FakeGateway:
        return gateway

    monkeypatch.setattr(structured_logging, "StructuredLogGateway", _gateway_factory)

    await structured_logging.emit_structured_log(
        event_type="CustomEvent",
        event_data={"foo": "bar"},
    )

    assert gateway.closed is True
    assert gateway.calls
    assert gateway.calls[0]["event_type"] == "CustomEvent"
    assert gateway.calls[0]["event_data"] == {"foo": "bar"}


@pytest.mark.asyncio
async def test_structured_task_decorator_logs(monkeypatch) -> None:
    gateway = _FakeGateway()

    def _gateway_factory() -> _FakeGateway:
        return gateway

    monkeypatch.setattr(structured_logging, "StructuredLogGateway", _gateway_factory)

    @structured_logging.structured_task()
    async def sample_task(user_id: str, value: int) -> int:
        return value + 1

    result = await sample_task(user_id="user-1", value=2)

    assert result == 3
    assert gateway.closed is True
    assert gateway.calls
    event_data = gateway.calls[0]["event_data"]
    assert event_data["status"] == "success"
    assert event_data["params"]["user_id"] == "user-1"
    assert event_data["params"]["value"] == 2
