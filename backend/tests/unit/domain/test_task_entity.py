"""Unit tests for Task entity methods."""

import datetime
from datetime import UTC

import pytest

from planned.core.exceptions import DomainError
from planned.domain import value_objects
from planned.domain.entities import ActionEntity, TaskEntity
from planned.infrastructure import data_objects


@pytest.fixture
def test_task(test_user_id: str) -> TaskEntity:
    """Create a test task."""
    task_def = data_objects.TaskDefinition(
        user_id=test_user_id,
        name="Test Task Definition",
        description="Test description",
        type=value_objects.TaskType.CHORE,
    )
    return TaskEntity(
        user_id=test_user_id,
        scheduled_date=datetime.date(2025, 11, 27),
        name="Test Task",
        status=value_objects.TaskStatus.NOT_STARTED,
        task_definition=task_def,
        category=value_objects.TaskCategory.HYGIENE,
        frequency=value_objects.TaskFrequency.DAILY,
    )


@pytest.mark.parametrize(
    ("initial_status", "action_type", "expected_status", "should_complete"),
    [
        (
            value_objects.TaskStatus.NOT_STARTED,
            value_objects.ActionType.COMPLETE,
            value_objects.TaskStatus.COMPLETE,
            True,
        ),
        (
            value_objects.TaskStatus.PENDING,
            value_objects.ActionType.COMPLETE,
            value_objects.TaskStatus.COMPLETE,
            True,
        ),
        (
            value_objects.TaskStatus.READY,
            value_objects.ActionType.COMPLETE,
            value_objects.TaskStatus.COMPLETE,
            True,
        ),
        (
            value_objects.TaskStatus.NOT_STARTED,
            value_objects.ActionType.PUNT,
            value_objects.TaskStatus.PUNT,
            False,
        ),
        (
            value_objects.TaskStatus.PENDING,
            value_objects.ActionType.NOTIFY,
            value_objects.TaskStatus.PENDING,
            False,
        ),
    ],
)
def test_record_action_status_transitions(
    test_task: TaskEntity,
    initial_status: value_objects.TaskStatus,
    action_type: value_objects.ActionType,
    expected_status: value_objects.TaskStatus,
    should_complete: bool,
) -> None:
    """Test record_action handles status transitions correctly."""
    test_task.status = initial_status
    action = ActionEntity(type=action_type)

    old_status = test_task.record_action(action)

    assert old_status == initial_status
    assert test_task.status == expected_status
    assert len(test_task.actions) == 1
    assert test_task.actions[0].type == action_type
    if should_complete:
        assert test_task.completed_at is not None
    else:
        assert test_task.completed_at is None


def test_record_action_complete_already_complete(test_task: TaskEntity) -> None:
    """Test record_action raises error when completing already complete task."""
    test_task.status = value_objects.TaskStatus.COMPLETE
    action = ActionEntity(type=value_objects.ActionType.COMPLETE)

    with pytest.raises(DomainError, match="already complete"):
        test_task.record_action(action)


def test_record_action_punt_already_punted(test_task: TaskEntity) -> None:
    """Test record_action raises error when punting already punted task."""
    test_task.status = value_objects.TaskStatus.PUNT
    action = ActionEntity(type=value_objects.ActionType.PUNT)

    with pytest.raises(DomainError, match="already punted"):
        test_task.record_action(action)


def test_mark_pending(test_task: TaskEntity) -> None:
    """Test mark_pending changes status to PENDING."""
    test_task.status = value_objects.TaskStatus.NOT_STARTED

    old_status = test_task.mark_pending()

    assert old_status == value_objects.TaskStatus.NOT_STARTED
    assert test_task.status == value_objects.TaskStatus.PENDING


def test_mark_pending_already_pending(test_task: TaskEntity) -> None:
    """Test mark_pending returns same status if already pending."""
    test_task.status = value_objects.TaskStatus.PENDING

    old_status = test_task.mark_pending()

    assert old_status == value_objects.TaskStatus.PENDING
    assert test_task.status == value_objects.TaskStatus.PENDING


def test_mark_ready(test_task: TaskEntity) -> None:
    """Test mark_ready changes status to READY."""
    test_task.status = value_objects.TaskStatus.NOT_STARTED

    old_status = test_task.mark_ready()

    assert old_status == value_objects.TaskStatus.NOT_STARTED
    assert test_task.status == value_objects.TaskStatus.READY


def test_mark_ready_already_ready(test_task: TaskEntity) -> None:
    """Test mark_ready returns same status if already ready."""
    test_task.status = value_objects.TaskStatus.READY

    old_status = test_task.mark_ready()

    assert old_status == value_objects.TaskStatus.READY
    assert test_task.status == value_objects.TaskStatus.READY

