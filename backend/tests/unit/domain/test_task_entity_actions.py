"""Unit tests for TaskEntity record_action edge cases."""

from __future__ import annotations

from datetime import UTC, date as dt_date, datetime
from uuid import uuid4

import pytest

from lykke.core.exceptions import DomainError
from lykke.domain import value_objects
from lykke.domain.entities import TaskEntity
from lykke.domain.events.task_events import TaskStateUpdatedEvent


def _build_task(status: value_objects.TaskStatus) -> TaskEntity:
    return TaskEntity(
        user_id=uuid4(),
        scheduled_date=dt_date(2025, 11, 27),
        name="Task",
        status=status,
        type=value_objects.TaskType.WORK,
        category=value_objects.TaskCategory.WORK,
        frequency=value_objects.TaskFrequency.ONCE,
    )


def test_task_snooze_requires_timestamp() -> None:
    task = _build_task(value_objects.TaskStatus.READY)
    action = value_objects.Action(type=value_objects.ActionType.SNOOZE)

    with pytest.raises(DomainError, match="snoozed_until"):
        task.record_action(action)


def test_task_snooze_allows_completed_task() -> None:
    task = _build_task(value_objects.TaskStatus.COMPLETE)
    completed_at = datetime(2025, 11, 27, 8, 0, tzinfo=UTC)
    task.completed_at = completed_at
    action = value_objects.Action(
        type=value_objects.ActionType.SNOOZE,
        data={"snoozed_until": datetime(2025, 11, 27, 10, 0, tzinfo=UTC)},
    )

    task.record_action(action)

    assert task.status == value_objects.TaskStatus.SNOOZE
    assert task.snoozed_until == action.data["snoozed_until"]
    assert task.completed_at is None


def test_task_records_other_actions_without_status_change() -> None:
    task = _build_task(value_objects.TaskStatus.READY)
    action = value_objects.Action(type=value_objects.ActionType.DELETE)

    task.record_action(action)

    assert task.status == value_objects.TaskStatus.READY
    events = task.collect_events()
    assert any(isinstance(event, TaskStateUpdatedEvent) for event in events)
    assert any(isinstance(event, TaskStateUpdatedEvent) for event in events)
