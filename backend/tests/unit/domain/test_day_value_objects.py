"""Unit tests for day value objects."""

import datetime
from datetime import UTC

import pytest

from lykke.domain.value_objects.day import (
    Alarm,
    AlarmType,
    DayContext,
    DayMode,
    DayStatus,
    DayTag,
    Reminder,
    ReminderStatus,
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
        (DayStatus.STARTED, "STARTED"),
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
    assert context.routines == []
    assert context.brain_dump_items == []


def test_day_context_defaults() -> None:
    """Test DayContext has default empty lists."""
    from uuid import uuid4

    from lykke.domain.entities import DayEntity

    test_user_id = uuid4()
    day = DayEntity(
        user_id=test_user_id,
        date=datetime.date(2025, 11, 27),
        status=DayStatus.UNSCHEDULED,
    )
    context = DayContext(day=day)
    assert context.calendar_entries == []
    assert context.tasks == []
    assert context.routines == []
    assert context.brain_dump_items == []


@pytest.mark.parametrize(
    ("status", "expected_value"),
    [
        (ReminderStatus.INCOMPLETE, "INCOMPLETE"),
        (ReminderStatus.COMPLETE, "COMPLETE"),
        (ReminderStatus.PUNT, "PUNT"),
    ],
)
def test_reminder_status_values(status: ReminderStatus, expected_value: str) -> None:
    """Test ReminderStatus enum values."""
    assert status.value == expected_value


def test_reminder_creation() -> None:
    """Test Reminder can be created with required fields."""
    from uuid import uuid4

    reminder = Reminder(
        id=uuid4(),
        name="Test Reminder",
        status=ReminderStatus.INCOMPLETE,
    )
    assert reminder.name == "Test Reminder"
    assert reminder.status == ReminderStatus.INCOMPLETE
    assert reminder.created_at is None


def test_reminder_creation_with_defaults() -> None:
    """Test Reminder uses default values when not specified."""
    from uuid import uuid4

    reminder = Reminder(
        id=uuid4(),
        name="Test Reminder",
    )
    assert reminder.name == "Test Reminder"
    assert reminder.status == ReminderStatus.INCOMPLETE
    assert reminder.created_at is None


def test_reminder_creation_with_all_fields() -> None:
    """Test Reminder can be created with all fields."""
    from uuid import uuid4

    created_at = datetime.datetime(2025, 11, 27, 12, 0, 0, tzinfo=UTC)
    reminder = Reminder(
        id=uuid4(),
        name="Test Reminder",
        status=ReminderStatus.COMPLETE,
        created_at=created_at,
    )
    assert reminder.name == "Test Reminder"
    assert reminder.status == ReminderStatus.COMPLETE
    assert reminder.created_at == created_at


@pytest.mark.parametrize(
    ("alarm_type", "expected_value"),
    [
        (AlarmType.URL, "URL"),
        (AlarmType.GENERIC, "GENERIC"),
    ],
)
def test_alarm_type_values(alarm_type: AlarmType, expected_value: str) -> None:
    """Test AlarmType enum values."""
    assert alarm_type.value == expected_value


def test_alarm_creation_with_defaults() -> None:
    """Test Alarm uses default values when not specified."""
    alarm = Alarm(
        name="Morning alarm",
        time=datetime.time(8, 30),
    )
    assert alarm.name == "Morning alarm"
    assert alarm.time == datetime.time(8, 30)
    assert alarm.datetime is None
    assert alarm.type == AlarmType.URL
    assert alarm.url == ""


def test_alarm_creation_with_all_fields() -> None:
    """Test Alarm can be created with all fields."""
    alarm_dt = datetime.datetime(2025, 11, 27, 8, 30, tzinfo=UTC)
    alarm = Alarm(
        name="Start work",
        time=datetime.time(8, 30),
        datetime=alarm_dt,
        type=AlarmType.GENERIC,
        url="https://example.com",
    )
    assert alarm.name == "Start work"
    assert alarm.time == datetime.time(8, 30)
    assert alarm.datetime == alarm_dt
    assert alarm.type == AlarmType.GENERIC
    assert alarm.url == "https://example.com"
