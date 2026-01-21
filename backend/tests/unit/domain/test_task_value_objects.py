"""Unit tests for task value objects."""

import datetime
from datetime import time

import pytest
from lykke.domain.value_objects.task import TaskSchedule, TimingType


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
