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
from lykke.application.events.handlers.task_status_logger import TaskStatusLoggerHandler
from lykke.application.worker_schedule import (
    reset_current_workers_to_schedule,
    set_current_workers_to_schedule,
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
async def test_smart_notification_trigger_enqueues_task() -> None:
    from lykke.presentation.workers import tasks as worker_tasks
    from lykke.presentation.workers.tasks.post_commit_workers import WorkersToSchedule
    from lykke.presentation.workers.tasks.registry import WorkerRegistry

    user_id = uuid4()
    recorder = _TaskRecorder(calls=[])
    workers_to_schedule = WorkersToSchedule(WorkerRegistry())

    worker_tasks.set_worker_override(
        worker_tasks.evaluate_smart_notification_task,
        recorder,
    )
    token = set_current_workers_to_schedule(workers_to_schedule)
    try:
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
        await workers_to_schedule.flush()
        assert recorder.calls == [
            {"user_id": user_id, "triggered_by": "task_completed"}
        ]
    finally:
        reset_current_workers_to_schedule(token)
        worker_tasks.clear_worker_overrides()


@pytest.mark.asyncio
async def test_smart_notification_trigger_handles_errors() -> None:
    from lykke.presentation.workers import tasks as worker_tasks
    from lykke.presentation.workers.tasks.post_commit_workers import WorkersToSchedule
    from lykke.presentation.workers.tasks.registry import WorkerRegistry

    user_id = uuid4()
    workers_to_schedule = WorkersToSchedule(WorkerRegistry())

    class _Worker:
        async def kiq(self, **_: Any) -> None:
            raise RuntimeError("boom")

    worker_tasks.set_worker_override(
        worker_tasks.evaluate_smart_notification_task,
        _Worker(),
    )
    token = set_current_workers_to_schedule(workers_to_schedule)
    try:
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
        await workers_to_schedule.flush()
    finally:
        reset_current_workers_to_schedule(token)
        worker_tasks.clear_worker_overrides()


@pytest.mark.asyncio
async def test_smart_notification_trigger_handles_status_change() -> None:
    from lykke.presentation.workers import tasks as worker_tasks
    from lykke.presentation.workers.tasks.post_commit_workers import WorkersToSchedule
    from lykke.presentation.workers.tasks.registry import WorkerRegistry

    user_id = uuid4()
    recorder = _TaskRecorder(calls=[])
    workers_to_schedule = WorkersToSchedule(WorkerRegistry())

    worker_tasks.set_worker_override(
        worker_tasks.evaluate_smart_notification_task,
        recorder,
    )
    token = set_current_workers_to_schedule(workers_to_schedule)
    try:
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
        await workers_to_schedule.flush()
        assert recorder.calls == [
            {"user_id": user_id, "triggered_by": "task_status_changed"}
        ]
    finally:
        reset_current_workers_to_schedule(token)
        worker_tasks.clear_worker_overrides()


@pytest.mark.asyncio
async def test_smart_notification_trigger_handles_unknown_event() -> None:
    from lykke.presentation.workers import tasks as worker_tasks
    from lykke.presentation.workers.tasks.post_commit_workers import WorkersToSchedule
    from lykke.presentation.workers.tasks.registry import WorkerRegistry

    user_id = uuid4()
    recorder = _TaskRecorder(calls=[])
    workers_to_schedule = WorkersToSchedule(WorkerRegistry())

    @dataclass(frozen=True, kw_only=True)
    class _OtherEvent(DomainEvent):
        pass

    worker_tasks.set_worker_override(
        worker_tasks.evaluate_smart_notification_task,
        recorder,
    )
    token = set_current_workers_to_schedule(workers_to_schedule)
    try:
        handler = SmartNotificationTriggerHandler(
            create_read_only_repos_double(), user_id
        )
        await handler.handle(_OtherEvent(user_id=user_id))
        await workers_to_schedule.flush()
        assert recorder.calls == [{"user_id": user_id, "triggered_by": "task_event"}]
    finally:
        reset_current_workers_to_schedule(token)
        worker_tasks.clear_worker_overrides()


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
