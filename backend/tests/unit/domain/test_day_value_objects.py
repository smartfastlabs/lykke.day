"""Unit tests for day value objects."""

import datetime
from datetime import UTC

import pytest

from planned.domain.value_objects.day import (
    DayContext,
    DayMode,
    DayStatus,
    DayTag,
)


@pytest.mark.parametrize(
    ("tag", "expected_value"),
    [
        (DayTag.WEEKEND, "WEEKEND"),
        (DayTag.VACATION, "VACATION"),
        (DayTag.WORKDAY, "WORKDAY"),
    ],
)
def test_day_tag_values(tag: DayTag, expected_value: str) -> None:
    """Test DayTag enum values."""
    assert tag.value == expected_value


@pytest.mark.parametrize(
    ("status", "expected_value"),
    [
        (DayStatus.UNSCHEDULED, "UNSCHEDULED"),
        (DayStatus.SCHEDULED, "SCHEDULED"),
        (DayStatus.IN_PROGRESS, "IN_PROGRESS"),
        (DayStatus.COMPLETE, "COMPLETE"),
    ],
)
def test_day_status_values(status: DayStatus, expected_value: str) -> None:
    """Test DayStatus enum values."""
    assert status.value == expected_value


@pytest.mark.parametrize(
    ("mode", "expected_value"),
    [
        (DayMode.PRE_DAY, "PRE_DAY"),
        (DayMode.LYKKE, "LYKKE"),
        (DayMode.WORK, "WORK"),
        (DayMode.POST_DAY, "POST_DAY"),
    ],
)
def test_day_mode_values(mode: DayMode, expected_value: str) -> None:
    """Test DayMode enum values."""
    assert mode.value == expected_value


def test_day_context_creation(test_user_id: str) -> None:
    """Test DayContext can be created with a day."""
    from planned.domain.entities import Day

    day = Day(
        user_id=test_user_id,
        date=datetime.date(2025, 11, 27),
        status=DayStatus.UNSCHEDULED,
    )
    context = DayContext(day=day)
    assert context.day == day
    assert context.calendar_entries == []
    assert context.tasks == []
    assert context.messages == []


def test_day_context_defaults() -> None:
    """Test DayContext has default empty lists."""
    from planned.domain.entities import Day
    from uuid import uuid4

    test_user_id = uuid4()
    day = Day(
        user_id=test_user_id,
        date=datetime.date(2025, 11, 27),
        status=DayStatus.UNSCHEDULED,
    )
    context = DayContext(day=day)
    assert context.calendar_entries == []
    assert context.tasks == []
    assert context.messages == []

