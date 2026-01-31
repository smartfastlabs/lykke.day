"""Unit tests for TaskEntity with TaskType.REMINDER (reminders as tasks)."""

import datetime
from datetime import date as dt_date
from uuid import uuid4

import pytest

from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity, TaskEntity
from lykke.domain.events.task_events import TaskCompletedEvent, TaskPuntedEvent


@pytest.fixture
def test_day(test_user_id: str) -> DayEntity:
    """Create a test day."""
    template = DayTemplateEntity(
        user_id=test_user_id,
        slug="default",
        routine_definition_ids=[],
        time_blocks=[],
    )
    return DayEntity.create_for_date(
        dt_date(2025, 11, 27),
        user_id=test_user_id,
        template=template,
    )


def test_reminder_task_has_reminder_type(test_user_id: str) -> None:
    """Test creating a task with TaskType.REMINDER."""
    task = TaskEntity(
        user_id=test_user_id,
        scheduled_date=dt_date(2025, 11, 27),
        name="Test Reminder",
        status=value_objects.TaskStatus.NOT_STARTED,
        type=value_objects.TaskType.REMINDER,
        category=value_objects.TaskCategory.PLANNING,
        frequency=value_objects.TaskFrequency.ONCE,
    )
    assert task.type == value_objects.TaskType.REMINDER
    assert task.name == "Test Reminder"
    assert task.status == value_objects.TaskStatus.NOT_STARTED


def test_reminder_task_complete_via_record_task_action(
    test_day: DayEntity, test_user_id: str
) -> None:
    """Test completing a reminder task via Day.record_task_action (COMPLETE)."""
    task = TaskEntity(
        user_id=test_user_id,
        scheduled_date=test_day.date,
        name="Test Reminder",
        status=value_objects.TaskStatus.NOT_STARTED,
        type=value_objects.TaskType.REMINDER,
        category=value_objects.TaskCategory.PLANNING,
        frequency=value_objects.TaskFrequency.ONCE,
    )
    action = value_objects.Action(type=value_objects.ActionType.COMPLETE)

    updated = test_day.record_task_action(task, action)

    assert updated.status == value_objects.TaskStatus.COMPLETE
    assert updated.type == value_objects.TaskType.REMINDER
    assert updated.completed_at is not None
    events = test_day.collect_events()
    assert any(isinstance(e, TaskCompletedEvent) for e in events)


def test_reminder_task_punt_via_record_task_action(
    test_day: DayEntity, test_user_id: str
) -> None:
    """Test punting a reminder task via Day.record_task_action (PUNT)."""
    task = TaskEntity(
        user_id=test_user_id,
        scheduled_date=test_day.date,
        name="Test Reminder",
        status=value_objects.TaskStatus.NOT_STARTED,
        type=value_objects.TaskType.REMINDER,
        category=value_objects.TaskCategory.PLANNING,
        frequency=value_objects.TaskFrequency.ONCE,
    )
    action = value_objects.Action(type=value_objects.ActionType.PUNT)

    updated = test_day.record_task_action(task, action)

    assert updated.status == value_objects.TaskStatus.PUNT
    assert updated.type == value_objects.TaskType.REMINDER
    events = test_day.collect_events()
    assert any(isinstance(e, TaskPuntedEvent) for e in events)
