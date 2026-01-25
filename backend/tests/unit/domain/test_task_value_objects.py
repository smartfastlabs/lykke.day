"""Unit tests for task value objects."""

from datetime import time

from lykke.domain.value_objects.routine_definition import TimeWindow


def test_time_window_with_all_times() -> None:
    """Test TimeWindow with all time fields set."""
    time_window = TimeWindow(
        available_time=time(8, 0),
        start_time=time(9, 0),
        end_time=time(10, 0),
        cutoff_time=time(18, 0),
    )
    assert time_window.available_time == time(8, 0)
    assert time_window.start_time == time(9, 0)
    assert time_window.end_time == time(10, 0)
    assert time_window.cutoff_time == time(18, 0)


def test_time_window_defaults() -> None:
    """Test TimeWindow defaults to empty fields."""
    time_window = TimeWindow()
    assert time_window.available_time is None
    assert time_window.start_time is None
    assert time_window.end_time is None
    assert time_window.cutoff_time is None
