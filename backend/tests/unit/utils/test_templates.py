"""Unit tests for template formatting helpers."""

from datetime import UTC, date, datetime

import pytest

from lykke.core.utils.templates import fmt_date, fmt_datetime


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (date(2026, 2, 2), "2026-02-02 (today)"),
        (date(2026, 2, 3), "2026-02-03 (tomorrow)"),
        (date(2026, 2, 7), "2026-02-07 (in 5 days)"),
        (date(2026, 1, 31), "2026-01-31 (2 days ago)"),
    ],
)
def test_fmt_date_relative_labels(value: date, expected: str) -> None:
    current_time = datetime(2026, 2, 2, 9, 0, tzinfo=UTC)
    result = fmt_date({"current_time": current_time}, value)
    assert result == expected


def test_fmt_date_without_current_time() -> None:
    result = fmt_date({}, date(2026, 2, 2))
    assert result == "2026-02-02"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (datetime(2026, 2, 2, 16, 0, tzinfo=UTC), "Today at 4:00pm"),
        (datetime(2026, 2, 3, 9, 15, tzinfo=UTC), "Tomorrow at 9:15am"),
        (datetime(2026, 2, 1, 21, 30, tzinfo=UTC), "Yesterday at 9:30pm"),
        (datetime(2026, 2, 7, 10, 22, tzinfo=UTC), "2026-02-07 at 10:22am"),
    ],
)
def test_fmt_datetime_day_labels(value: datetime, expected: str) -> None:
    current_time = datetime(2026, 2, 2, 10, 0, tzinfo=UTC)
    result = fmt_datetime({"current_time": current_time}, value)
    assert result == expected


def test_fmt_datetime_without_current_time() -> None:
    value = datetime(2026, 2, 7, 10, 22, tzinfo=UTC)
    result = fmt_datetime({}, value)
    assert result == "2026-02-07 at 10:22am"
