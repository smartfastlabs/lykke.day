"""Unit tests for task value objects."""

import datetime
from datetime import time

import pytest

from planned.domain.value_objects.task import (
    TaskCategory,
    TaskFrequency,
    TaskSchedule,
    TaskStatus,
    TaskTag,
    TaskType,
    TimingType,
)


@pytest.mark.parametrize(
    ("tag", "expected_value"),
    [
        (TaskTag.AVOIDANT, "AVOIDANT"),
        (TaskTag.FORGETTABLE, "FORGETTABLE"),
        (TaskTag.IMPORTANT, "IMPORTANT"),
        (TaskTag.URGENT, "URGENT"),
        (TaskTag.FUN, "FUN"),
    ],
)
def test_task_tag_values(tag: TaskTag, expected_value: str) -> None:
    """Test TaskTag enum values."""
    assert tag.value == expected_value


@pytest.mark.parametrize(
    ("frequency", "expected_value"),
    [
        (TaskFrequency.DAILY, "DAILY"),
        (TaskFrequency.WEEKLY, "WEEKLY"),
        (TaskFrequency.MONTHLY, "MONTHLY"),
        (TaskFrequency.YEARLY, "YEARLY"),
        (TaskFrequency.ONCE, "ONCE"),
        (TaskFrequency.BI_WEEKLY, "BI_WEEKLY"),
        (TaskFrequency.CUSTOM_WEEKLY, "CUSTOM_WEEKLY"),
        (TaskFrequency.WEEK_DAYS, "WORK_DAYS"),
        (TaskFrequency.WEEKEND_DAYS, "WEEKENDS"),
    ],
)
def test_task_frequency_values(
    frequency: TaskFrequency, expected_value: str
) -> None:
    """Test TaskFrequency enum values."""
    assert frequency.value == expected_value


@pytest.mark.parametrize(
    ("category", "expected_value"),
    [
        (TaskCategory.HYGIENE, "HYGIENE"),
        (TaskCategory.NUTRITION, "NUTRITION"),
        (TaskCategory.HEALTH, "HEALTH"),
        (TaskCategory.PET, "PET"),
        (TaskCategory.HOUSE, "HOUSE"),
    ],
)
def test_task_category_values(
    category: TaskCategory, expected_value: str
) -> None:
    """Test TaskCategory enum values."""
    assert category.value == expected_value


@pytest.mark.parametrize(
    ("task_type", "expected_value"),
    [
        (TaskType.MEAL, "MEAL"),
        (TaskType.EVENT, "EVENT"),
        (TaskType.CHORE, "CHORE"),
        (TaskType.ERRAND, "ERRAND"),
        (TaskType.ACTIVITY, "ACTIVITY"),
    ],
)
def test_task_type_values(task_type: TaskType, expected_value: str) -> None:
    """Test TaskType enum values."""
    assert task_type.value == expected_value


@pytest.mark.parametrize(
    ("status", "expected_value"),
    [
        (TaskStatus.COMPLETE, "COMPLETE"),
        (TaskStatus.NOT_READY, "NOT_READY"),
        (TaskStatus.READY, "READY"),
        (TaskStatus.PUNT, "PUNT"),
        (TaskStatus.NOT_STARTED, "NOT_STARTED"),
        (TaskStatus.PENDING, "PENDING"),
    ],
)
def test_task_status_values(status: TaskStatus, expected_value: str) -> None:
    """Test TaskStatus enum values."""
    assert status.value == expected_value


@pytest.mark.parametrize(
    ("timing_type", "expected_value"),
    [
        (TimingType.DEADLINE, "DEADLINE"),
        (TimingType.FIXED_TIME, "FIXED_TIME"),
        (TimingType.TIME_WINDOW, "TIME_WINDOW"),
        (TimingType.FLEXIBLE, "FLEXIBLE"),
    ],
)
def test_timing_type_values(
    timing_type: TimingType, expected_value: str
) -> None:
    """Test TimingType enum values."""
    assert timing_type.value == expected_value


def test_task_schedule_with_all_times() -> None:
    """Test TaskSchedule with all time fields set."""
    schedule = TaskSchedule(
        available_time=time(8, 0),
        start_time=time(9, 0),
        end_time=time(10, 0),
        timing_type=TimingType.TIME_WINDOW,
    )
    assert schedule.available_time == time(8, 0)
    assert schedule.start_time == time(9, 0)
    assert schedule.end_time == time(10, 0)
    assert schedule.timing_type == TimingType.TIME_WINDOW


def test_task_schedule_bool_true() -> None:
    """Test TaskSchedule __bool__ returns True when times are set."""
    schedule = TaskSchedule(
        start_time=time(9, 0),
        timing_type=TimingType.FIXED_TIME,
    )
    assert bool(schedule) is True


def test_task_schedule_bool_false() -> None:
    """Test TaskSchedule __bool__ returns False when no times are set."""
    schedule = TaskSchedule(timing_type=TimingType.FLEXIBLE)
    assert bool(schedule) is False


@pytest.mark.parametrize(
    ("available_time", "start_time", "end_time", "expected"),
    [
        (time(8, 0), None, None, True),
        (None, time(9, 0), None, True),
        (None, None, time(10, 0), True),
        (None, None, None, False),
    ],
)
def test_task_schedule_bool_variations(
    available_time: time | None,
    start_time: time | None,
    end_time: time | None,
    expected: bool,
) -> None:
    """Test TaskSchedule __bool__ with various time combinations."""
    schedule = TaskSchedule(
        available_time=available_time,
        start_time=start_time,
        end_time=end_time,
        timing_type=TimingType.FLEXIBLE,
    )
    assert bool(schedule) == expected

