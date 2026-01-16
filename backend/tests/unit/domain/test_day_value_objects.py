"""Unit tests for day value objects."""

import datetime
from datetime import UTC

import pytest

from lykke.domain.value_objects.day import (
    DayContext,
    DayMode,
    DayStatus,
    DayTag,
    Goal,
    GoalStatus,
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
    from lykke.domain.entities import DayEntity

    day = DayEntity(
        user_id=test_user_id,
        date=datetime.date(2025, 11, 27),
        status=DayStatus.UNSCHEDULED,
    )
    context = DayContext(day=day)
    assert context.day == day
    assert context.calendar_entries == []
    assert context.tasks == []


def test_day_context_defaults() -> None:
    """Test DayContext has default empty lists."""
    from lykke.domain.entities import DayEntity
    from uuid import uuid4

    test_user_id = uuid4()
    day = DayEntity(
        user_id=test_user_id,
        date=datetime.date(2025, 11, 27),
        status=DayStatus.UNSCHEDULED,
    )
    context = DayContext(day=day)
    assert context.calendar_entries == []
    assert context.tasks == []


@pytest.mark.parametrize(
    ("status", "expected_value"),
    [
        (GoalStatus.INCOMPLETE, "INCOMPLETE"),
        (GoalStatus.COMPLETE, "COMPLETE"),
        (GoalStatus.PUNT, "PUNT"),
    ],
)
def test_goal_status_values(status: GoalStatus, expected_value: str) -> None:
    """Test GoalStatus enum values."""
    assert status.value == expected_value


def test_goal_creation() -> None:
    """Test Goal can be created with required fields."""
    from uuid import uuid4

    goal = Goal(
        id=uuid4(),
        name="Test Goal",
        status=GoalStatus.INCOMPLETE,
    )
    assert goal.name == "Test Goal"
    assert goal.status == GoalStatus.INCOMPLETE
    assert goal.created_at is None


def test_goal_creation_with_defaults() -> None:
    """Test Goal uses default values when not specified."""
    from uuid import uuid4

    goal = Goal(
        id=uuid4(),
        name="Test Goal",
    )
    assert goal.name == "Test Goal"
    assert goal.status == GoalStatus.INCOMPLETE
    assert goal.created_at is None


def test_goal_creation_with_all_fields() -> None:
    """Test Goal can be created with all fields."""
    from uuid import uuid4

    created_at = datetime.datetime(2025, 11, 27, 12, 0, 0, tzinfo=UTC)
    goal = Goal(
        id=uuid4(),
        name="Test Goal",
        status=GoalStatus.COMPLETE,
        created_at=created_at,
    )
    assert goal.name == "Test Goal"
    assert goal.status == GoalStatus.COMPLETE
    assert goal.created_at == created_at

