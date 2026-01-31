"""Unit tests for day value objects."""

import datetime
from datetime import UTC
from uuid import uuid4

import pytest

from lykke.domain.entities import DayEntity
from lykke.domain.value_objects.day import (
    Alarm,
    AlarmStatus,
    AlarmType,
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
    assert alarm.id is not None
    assert alarm.name == "Morning alarm"
    assert alarm.time == datetime.time(8, 30)
    assert alarm.datetime is None
    assert alarm.type == AlarmType.URL
    assert alarm.url == ""
    assert alarm.status == AlarmStatus.ACTIVE
    assert alarm.snoozed_until is None


def test_alarm_creation_with_all_fields() -> None:
    """Test Alarm can be created with all fields."""
    alarm_dt = datetime.datetime(2025, 11, 27, 8, 30, tzinfo=UTC)
    alarm = Alarm(
        id=uuid4(),
        name="Start work",
        time=datetime.time(8, 30),
        datetime=alarm_dt,
        type=AlarmType.GENERIC,
        url="https://example.com",
        status=AlarmStatus.SNOOZED,
        snoozed_until=alarm_dt,
    )
    assert alarm.id is not None
    assert alarm.name == "Start work"
    assert alarm.time == datetime.time(8, 30)
    assert alarm.datetime == alarm_dt
    assert alarm.type == AlarmType.GENERIC
    assert alarm.url == "https://example.com"
    assert alarm.status == AlarmStatus.SNOOZED
    assert alarm.snoozed_until == alarm_dt
