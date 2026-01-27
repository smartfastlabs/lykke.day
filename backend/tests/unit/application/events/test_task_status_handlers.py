"""Unit tests for task status related handlers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from lykke.application.events.handlers.smart_notification_trigger import (
    SmartNotificationTriggerHandler,
)
from lykke.application.events.handlers.task_status_logger import (
    TaskStatusLoggerHandler,
)
from lykke.domain.events.base import DomainEvent
from lykke.domain.events.task_events import (
    TaskCompletedEvent,
    TaskPuntedEvent,
    TaskStatusChangedEvent,
)
from tests.support.dobles import create_read_only_repos_double


@dataclass
class _TaskRecorder:
    calls: list[dict[str, Any]]

    async def kiq(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)


@pytest.mark.asyncio
async def test_smart_notification_trigger_enqueues_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    recorder = _TaskRecorder(calls=[])

    monkeypatch.setattr(
        "lykke.presentation.workers.tasks.evaluate_smart_notification_task",
        recorder,
    )

    handler = SmartNotificationTriggerHandler(
        create_read_only_repos_double(), user_id
    )
    event = TaskCompletedEvent(
        user_id=user_id,
        task_id=uuid4(),
        completed_at=datetime.now(UTC),
        task_scheduled_date=datetime(2025, 11, 27, tzinfo=UTC).date(),
        task_name="Task",
        task_type="work",
        task_category="work",
        entity_id=uuid4(),
        entity_type="task",
        entity_date=datetime(2025, 11, 27, tzinfo=UTC).date(),
    )

    await handler.handle(event)

    assert recorder.calls == [
        {"user_id": user_id, "triggered_by": "task_completed"}
    ]


@pytest.mark.asyncio
async def test_smart_notification_trigger_handles_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()

    class _Task:
        async def kiq(self, **_: Any) -> None:
            raise RuntimeError("boom")

    monkeypatch.setattr(
        "lykke.presentation.workers.tasks.evaluate_smart_notification_task",
        _Task(),
    )

    handler = SmartNotificationTriggerHandler(
        create_read_only_repos_double(), user_id
    )
    event = TaskPuntedEvent(
        user_id=user_id,
        task_id=uuid4(),
        old_status="ready",
        new_status="punt",
        task_scheduled_date=datetime(2025, 11, 27, tzinfo=UTC).date(),
        task_name="Task",
        task_type="work",
        task_category="work",
        entity_id=uuid4(),
        entity_type="task",
        entity_date=datetime(2025, 11, 27, tzinfo=UTC).date(),
    )

    await handler.handle(event)


@pytest.mark.asyncio
async def test_smart_notification_trigger_handles_status_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    recorder = _TaskRecorder(calls=[])

    monkeypatch.setattr(
        "lykke.presentation.workers.tasks.evaluate_smart_notification_task",
        recorder,
    )

    handler = SmartNotificationTriggerHandler(
        create_read_only_repos_double(), user_id
    )
    event = TaskStatusChangedEvent(
        user_id=user_id,
        task_id=uuid4(),
        old_status="ready",
        new_status="complete",
    )

    await handler.handle(event)

    assert recorder.calls == [
        {"user_id": user_id, "triggered_by": "task_status_changed"}
    ]


@pytest.mark.asyncio
async def test_smart_notification_trigger_handles_unknown_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    recorder = _TaskRecorder(calls=[])

    @dataclass(frozen=True, kw_only=True)
    class _OtherEvent(DomainEvent):
        pass

    monkeypatch.setattr(
        "lykke.presentation.workers.tasks.evaluate_smart_notification_task",
        recorder,
    )

    handler = SmartNotificationTriggerHandler(
        create_read_only_repos_double(), user_id
    )

    await handler.handle(_OtherEvent(user_id=user_id))

    assert recorder.calls == [
        {"user_id": user_id, "triggered_by": "task_event"}
    ]


@pytest.mark.asyncio
async def test_task_status_logger_handles_events() -> None:
    user_id = uuid4()
    handler = TaskStatusLoggerHandler(create_read_only_repos_double(), user_id)

    await handler.handle(
        TaskStatusChangedEvent(
            user_id=user_id,
            task_id=uuid4(),
            old_status="ready",
            new_status="complete",
        )
    )
    await handler.handle(
        TaskCompletedEvent(
            user_id=user_id,
            task_id=uuid4(),
            completed_at=datetime.now(UTC),
            task_scheduled_date=datetime(2025, 11, 27, tzinfo=UTC).date(),
            task_name="Task",
            task_type="work",
            task_category="work",
            entity_id=uuid4(),
            entity_type="task",
            entity_date=datetime(2025, 11, 27, tzinfo=UTC).date(),
        )
    )

    class _OtherEvent:
        pass

    await handler.handle(_OtherEvent())  # type: ignore[arg-type]
