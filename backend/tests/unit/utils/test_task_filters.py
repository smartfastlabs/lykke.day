"""Unit tests for task filtering utilities."""

import datetime
from datetime import UTC, timedelta

import pytest
from freezegun import freeze_time

from lykke.core.utils.task_filters import (
    calculate_cutoff_time,
    filter_upcoming_tasks,
    is_task_eligible_for_upcoming,
)
from lykke.domain import value_objects
from lykke.domain.entities import TaskEntity
from lykke.infrastructure import data_objects


@pytest.fixture
def test_task_pending(test_user_id: str) -> TaskEntity:
    """Create a pending task for testing."""
    task_def = data_objects.TaskDefinition(
        user_id=test_user_id,
        name="Task Def",
        description="Test",
        type=value_objects.TaskType.CHORE,
    )
    return TaskEntity(
        user_id=test_user_id,
        scheduled_date=datetime.date(2025, 11, 27),
        name="Test Task",
        status=value_objects.TaskStatus.PENDING,
        task_definition=task_def,
        category=value_objects.TaskCategory.HYGIENE,
        frequency=value_objects.TaskFrequency.DAILY,
    )


@pytest.fixture
def test_task_with_schedule(test_user_id: str) -> TaskEntity:
    """Create a task with schedule for testing."""
    task_def = data_objects.TaskDefinition(
        user_id=test_user_id,
        name="Task Def",
        description="Test",
        type=value_objects.TaskType.CHORE,
    )
    schedule = value_objects.TaskSchedule(
        start_time=datetime.time(10, 0),
        end_time=datetime.time(12, 0),
        timing_type=value_objects.TimingType.TIME_WINDOW,
    )
    return TaskEntity(
        user_id=test_user_id,
        scheduled_date=datetime.date(2025, 11, 27),
        name="Scheduled Task",
        status=value_objects.TaskStatus.READY,
        task_definition=task_def,
        category=value_objects.TaskCategory.HYGIENE,
        frequency=value_objects.TaskFrequency.DAILY,
        schedule=schedule,
    )


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (value_objects.TaskStatus.PENDING, True),
        (value_objects.TaskStatus.NOT_STARTED, True),
        (value_objects.TaskStatus.READY, True),
        (value_objects.TaskStatus.COMPLETE, False),
        (value_objects.TaskStatus.PUNT, False),
        (value_objects.TaskStatus.NOT_READY, False),
    ],
)
def test_is_task_eligible_for_upcoming_status(
    test_user_id: str, status: value_objects.TaskStatus, expected: bool
) -> None:
    """Test task eligibility based on status."""
    task_def = data_objects.TaskDefinition(
        user_id=test_user_id,
        name="Task Def",
        description="Test",
        type=value_objects.TaskType.CHORE,
    )
    task = TaskEntity(
        user_id=test_user_id,
        scheduled_date=datetime.date(2025, 11, 27),
        name="Test Task",
        status=status,
        task_definition=task_def,
        category=value_objects.TaskCategory.HYGIENE,
        frequency=value_objects.TaskFrequency.DAILY,
        schedule=value_objects.TaskSchedule(
            start_time=datetime.time(10, 0),
            timing_type=value_objects.TimingType.FIXED_TIME,
        ),
    )
    with freeze_time("2025-11-27 09:00:00-06:00", real_asyncio=True):
        now = datetime.time(9, 0)
        cutoff = datetime.time(12, 0)
        result = is_task_eligible_for_upcoming(task, now, cutoff)
        assert result == expected


def test_is_task_eligible_for_upcoming_completed_task(
    test_task_with_schedule: TaskEntity,
) -> None:
    """Test completed tasks are not eligible."""
    test_task_with_schedule.completed_at = datetime.datetime.now(UTC)
    with freeze_time("2025-11-27 09:00:00-06:00", real_asyncio=True):
        now = datetime.time(9, 0)
        cutoff = datetime.time(12, 0)
        result = is_task_eligible_for_upcoming(
            test_task_with_schedule, now, cutoff
        )
        assert result is False


def test_is_task_eligible_for_upcoming_no_schedule(
    test_task_pending: TaskEntity,
) -> None:
    """Test tasks without schedule are not eligible."""
    with freeze_time("2025-11-27 09:00:00-06:00", real_asyncio=True):
        now = datetime.time(9, 0)
        cutoff = datetime.time(12, 0)
        result = is_task_eligible_for_upcoming(test_task_pending, now, cutoff)
        assert result is False


def test_is_task_eligible_for_upcoming_available_time_before_now(
    test_user_id: str,
) -> None:
    """Test task with available_time before now is eligible."""
    task_def = data_objects.TaskDefinition(
        user_id=test_user_id,
        name="Task Def",
        description="Test",
        type=value_objects.TaskType.CHORE,
    )
    schedule = value_objects.TaskSchedule(
        available_time=datetime.time(8, 0),
        start_time=datetime.time(10, 0),
        timing_type=value_objects.TimingType.FLEXIBLE,
    )
    task = TaskEntity(
        user_id=test_user_id,
        scheduled_date=datetime.date(2025, 11, 27),
        name="Test Task",
        status=value_objects.TaskStatus.READY,
        task_definition=task_def,
        category=value_objects.TaskCategory.HYGIENE,
        frequency=value_objects.TaskFrequency.DAILY,
        schedule=schedule,
    )
    with freeze_time("2025-11-27 09:00:00-06:00", real_asyncio=True):
        now = datetime.time(9, 0)
        cutoff = datetime.time(12, 0)
        result = is_task_eligible_for_upcoming(task, now, cutoff)
        assert result is True


def test_is_task_eligible_for_upcoming_available_time_after_now(
    test_user_id: str,
) -> None:
    """Test task with available_time after now is not eligible."""
    task_def = data_objects.TaskDefinition(
        user_id=test_user_id,
        name="Task Def",
        description="Test",
        type=value_objects.TaskType.CHORE,
    )
    schedule = value_objects.TaskSchedule(
        available_time=datetime.time(10, 0),
        start_time=datetime.time(11, 0),
        timing_type=value_objects.TimingType.FLEXIBLE,
    )
    task = TaskEntity(
        user_id=test_user_id,
        scheduled_date=datetime.date(2025, 11, 27),
        name="Test Task",
        status=value_objects.TaskStatus.READY,
        task_definition=task_def,
        category=value_objects.TaskCategory.HYGIENE,
        frequency=value_objects.TaskFrequency.DAILY,
        schedule=schedule,
    )
    with freeze_time("2025-11-27 09:00:00-06:00", real_asyncio=True):
        now = datetime.time(9, 0)
        cutoff = datetime.time(12, 0)
        result = is_task_eligible_for_upcoming(task, now, cutoff)
        assert result is False


def test_is_task_eligible_for_upcoming_start_time_after_cutoff(
    test_user_id: str,
) -> None:
    """Test task with start_time after cutoff is not eligible."""
    task_def = data_objects.TaskDefinition(
        user_id=test_user_id,
        name="Task Def",
        description="Test",
        type=value_objects.TaskType.CHORE,
    )
    schedule = value_objects.TaskSchedule(
        start_time=datetime.time(13, 0),
        timing_type=value_objects.TimingType.FIXED_TIME,
    )
    task = TaskEntity(
        user_id=test_user_id,
        scheduled_date=datetime.date(2025, 11, 27),
        name="Test Task",
        status=value_objects.TaskStatus.READY,
        task_definition=task_def,
        category=value_objects.TaskCategory.HYGIENE,
        frequency=value_objects.TaskFrequency.DAILY,
        schedule=schedule,
    )
    with freeze_time("2025-11-27 09:00:00-06:00", real_asyncio=True):
        now = datetime.time(9, 0)
        cutoff = datetime.time(12, 0)
        result = is_task_eligible_for_upcoming(task, now, cutoff)
        assert result is False


def test_is_task_eligible_for_upcoming_end_time_passed(
    test_user_id: str,
) -> None:
    """Test task with end_time that has passed is not eligible."""
    task_def = data_objects.TaskDefinition(
        user_id=test_user_id,
        name="Task Def",
        description="Test",
        type=value_objects.TaskType.CHORE,
    )
    schedule = value_objects.TaskSchedule(
        start_time=datetime.time(8, 0),
        end_time=datetime.time(9, 0),
        timing_type=value_objects.TimingType.TIME_WINDOW,
    )
    task = TaskEntity(
        user_id=test_user_id,
        scheduled_date=datetime.date(2025, 11, 27),
        name="Test Task",
        status=value_objects.TaskStatus.READY,
        task_definition=task_def,
        category=value_objects.TaskCategory.HYGIENE,
        frequency=value_objects.TaskFrequency.DAILY,
        schedule=schedule,
    )
    with freeze_time("2025-11-27 10:00:00-06:00", real_asyncio=True):
        now = datetime.time(10, 0)
        cutoff = datetime.time(12, 0)
        result = is_task_eligible_for_upcoming(task, now, cutoff)
        assert result is False


def test_calculate_cutoff_time(test_date: datetime.date) -> None:
    """Test calculate_cutoff_time calculates correct cutoff."""
    with freeze_time("2025-11-27 10:00:00-06:00", real_asyncio=True):
        look_ahead = timedelta(hours=2)
        result = calculate_cutoff_time(look_ahead)
        # Should be 2 hours ahead of 10:00, so 12:00
        assert result.hour == 12
        assert result.minute == 0


def test_calculate_cutoff_time_crosses_midnight(test_date: datetime.date) -> None:
    """Test calculate_cutoff_time handles crossing midnight."""
    with freeze_time("2025-11-27 23:00:00-06:00", real_asyncio=True):
        look_ahead = timedelta(hours=2)
        result = calculate_cutoff_time(look_ahead)
        # Should be 1:00 next day (25:00 -> 01:00)
        assert result.hour == 1
        assert result.minute == 0


def test_filter_upcoming_tasks(test_user_id: str) -> None:
    """Test filter_upcoming_tasks filters tasks correctly."""
    task_def = data_objects.TaskDefinition(
        user_id=test_user_id,
        name="Task Def",
        description="Test",
        type=value_objects.TaskType.CHORE,
    )
    eligible_task = TaskEntity(
        user_id=test_user_id,
        scheduled_date=datetime.date(2025, 11, 27),
        name="Eligible Task",
        status=value_objects.TaskStatus.READY,
        task_definition=task_def,
        category=value_objects.TaskCategory.HYGIENE,
        frequency=value_objects.TaskFrequency.DAILY,
        schedule=value_objects.TaskSchedule(
            start_time=datetime.time(11, 0),
            timing_type=value_objects.TimingType.FIXED_TIME,
        ),
    )
    ineligible_task = TaskEntity(
        user_id=test_user_id,
        scheduled_date=datetime.date(2025, 11, 27),
        name="Ineligible Task",
        status=value_objects.TaskStatus.COMPLETE,
        task_definition=task_def,
        category=value_objects.TaskCategory.HYGIENE,
        frequency=value_objects.TaskFrequency.DAILY,
        schedule=value_objects.TaskSchedule(
            start_time=datetime.time(11, 0),
            timing_type=value_objects.TimingType.FIXED_TIME,
        ),
    )
    no_schedule_task = TaskEntity(
        user_id=test_user_id,
        scheduled_date=datetime.date(2025, 11, 27),
        name="No Schedule Task",
        status=value_objects.TaskStatus.READY,
        task_definition=task_def,
        category=value_objects.TaskCategory.HYGIENE,
        frequency=value_objects.TaskFrequency.DAILY,
    )

    tasks = [eligible_task, ineligible_task, no_schedule_task]

    with freeze_time("2025-11-27 10:00:00-06:00", real_asyncio=True):
        look_ahead = timedelta(hours=2)
        result = filter_upcoming_tasks(tasks, look_ahead)
        assert len(result) == 1
        assert result[0].name == "Eligible Task"


def test_filter_upcoming_tasks_cutoff_before_now(test_user_id: str) -> None:
    """Test filter_upcoming_tasks returns all tasks when cutoff is before now."""
    task_def = data_objects.TaskDefinition(
        user_id=test_user_id,
        name="Task Def",
        description="Test",
        type=value_objects.TaskType.CHORE,
    )
    task = TaskEntity(
        user_id=test_user_id,
        scheduled_date=datetime.date(2025, 11, 27),
        name="Task",
        status=value_objects.TaskStatus.READY,
        task_definition=task_def,
        category=value_objects.TaskCategory.HYGIENE,
        frequency=value_objects.TaskFrequency.DAILY,
        schedule=value_objects.TaskSchedule(
            start_time=datetime.time(10, 0),
            timing_type=value_objects.TimingType.FIXED_TIME,
        ),
    )

    with freeze_time("2025-11-27 23:00:00-06:00", real_asyncio=True):
        # Look ahead of 2 hours would put cutoff at 1:00 next day
        # But since cutoff < now (1:00 < 23:00 in same day logic), returns all
        look_ahead = timedelta(hours=2)
        result = filter_upcoming_tasks([task], look_ahead)
        # When cutoff wraps around, it returns all tasks
        assert len(result) == 1

