"""Unit tests for routine domain service."""

import datetime

import pytest

from planned.core.utils import is_routine_active
from planned.domain.value_objects.routine import RoutineSchedule
from planned.domain.value_objects.task import TaskFrequency


@pytest.mark.parametrize(
    ("date", "weekdays", "expected"),
    [
        (datetime.date(2025, 11, 24), [0, 1, 2, 3, 4], True),  # Monday
        (datetime.date(2025, 11, 25), [0, 1, 2, 3, 4], True),  # Tuesday
        (datetime.date(2025, 11, 26), [0, 1, 2, 3, 4], True),  # Wednesday
        (datetime.date(2025, 11, 27), [0, 1, 2, 3, 4], True),  # Thursday
        (datetime.date(2025, 11, 28), [0, 1, 2, 3, 4], True),  # Friday
        (datetime.date(2025, 11, 29), [0, 1, 2, 3, 4], False),  # Saturday
        (datetime.date(2025, 11, 30), [0, 1, 2, 3, 4], False),  # Sunday
        (datetime.date(2025, 11, 29), [5, 6], True),  # Saturday
        (datetime.date(2025, 11, 30), [5, 6], True),  # Sunday
    ],
)
def test_is_routine_active_with_weekdays(
    date: datetime.date, weekdays: list[int], expected: bool
) -> None:
    """Test is_routine_active with specific weekdays."""
    from planned.domain.value_objects.routine import DayOfWeek

    schedule = RoutineSchedule(
        frequency=TaskFrequency.WEEKLY,
        weekdays=[DayOfWeek(d) for d in weekdays],
    )
    result = is_routine_active(schedule, date)
    assert result == expected


def test_is_routine_active_no_weekdays() -> None:
    """Test is_routine_active returns True when no weekdays specified."""
    schedule = RoutineSchedule(frequency=TaskFrequency.DAILY, weekdays=None)
    result = is_routine_active(
        schedule, datetime.date(2025, 11, 27)
    )
    assert result is True


@pytest.mark.parametrize(
    "frequency",
    [
        TaskFrequency.DAILY,
        TaskFrequency.WEEKLY,
        TaskFrequency.MONTHLY,
        TaskFrequency.YEARLY,
    ],
)
def test_is_routine_active_all_frequencies_no_weekdays(
    frequency: TaskFrequency,
) -> None:
    """Test is_routine_active with all frequencies when no weekdays."""
    schedule = RoutineSchedule(frequency=frequency, weekdays=None)
    result = is_routine_active(
        schedule, datetime.date(2025, 11, 27)
    )
    assert result is True

