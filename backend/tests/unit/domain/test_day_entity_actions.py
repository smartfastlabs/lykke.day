"""Unit tests for DayEntity alarms and task actions."""

from __future__ import annotations

from datetime import UTC, date as dt_date, datetime, time
from uuid import UUID, uuid4

import pytest

from lykke.core.exceptions import DomainError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity, TaskEntity
from lykke.domain.events.day_events import (
    AlarmAddedEvent,
    AlarmRemovedEvent,
    AlarmStatusChangedEvent,
    AlarmTriggeredEvent,
    DayCompletedEvent,
    DayScheduledEvent,
    DayUnscheduledEvent,
)
from lykke.domain.events.task_events import (
    TaskActionRecordedEvent,
    TaskCompletedEvent,
    TaskPuntedEvent,
    TaskStatusChangedEvent,
)


def _build_day(user_id: UUID) -> DayEntity:
    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_definition_ids=[],
        time_blocks=[],
    )
    return DayEntity.create_for_date(dt_date(2025, 11, 27), user_id, template)


def _build_task(user_id: UUID, date: dt_date) -> TaskEntity:
    return TaskEntity(
        user_id=user_id,
        scheduled_date=date,
        name="Task",
        status=value_objects.TaskStatus.READY,
        type=value_objects.TaskType.WORK,
        category=value_objects.TaskCategory.WORK,
        frequency=value_objects.TaskFrequency.ONCE,
    )


def test_day_schedule_and_unschedule_emit_events() -> None:
    user_id = uuid4()
    day = _build_day(user_id)
    template = day.template
    assert template is not None

    day.schedule(template)
    events = day.collect_events()
    assert isinstance(events[0], DayScheduledEvent)
    assert day.status == value_objects.DayStatus.SCHEDULED
    assert day.scheduled_at is not None

    day.unschedule()
    events = day.collect_events()
    assert any(isinstance(event, DayUnscheduledEvent) for event in events)
    assert day.status == value_objects.DayStatus.UNSCHEDULED


def test_day_unschedule_requires_scheduled_status() -> None:
    user_id = uuid4()
    day = _build_day(user_id)

    with pytest.raises(DomainError, match="Cannot unschedule day"):
        day.unschedule()


def test_day_schedule_raises_for_invalid_status() -> None:
    user_id = uuid4()
    day = _build_day(user_id)
    template = day.template
    assert template is not None
    day.status = value_objects.DayStatus.SCHEDULED

    with pytest.raises(DomainError, match="Cannot schedule day"):
        day.schedule(template)


def test_day_complete_requires_scheduled_status() -> None:
    user_id = uuid4()
    day = _build_day(user_id)

    with pytest.raises(DomainError, match="Cannot complete day"):
        day.complete()

    template = day.template
    assert template is not None
    day.schedule(template)
    day.collect_events()

    day.complete()
    events = day.collect_events()
    assert isinstance(events[0], DayCompletedEvent)
    assert day.status == value_objects.DayStatus.COMPLETE


def test_day_record_task_action_emits_events() -> None:
    user_id = uuid4()
    day = _build_day(user_id)
    task = _build_task(user_id, day.date)
    action = value_objects.Action(type=value_objects.ActionType.COMPLETE)

    day.record_task_action(task, action)
    events = day.collect_events()

    assert any(isinstance(event, TaskCompletedEvent) for event in events)
    assert any(isinstance(event, TaskStatusChangedEvent) for event in events)
    assert any(isinstance(event, TaskActionRecordedEvent) for event in events)


def test_day_record_task_action_without_status_change() -> None:
    user_id = uuid4()
    day = _build_day(user_id)
    task = _build_task(user_id, day.date)
    action = value_objects.Action(type=value_objects.ActionType.NOTIFY)

    day.record_task_action(task, action)
    events = day.collect_events()

    assert any(isinstance(event, TaskActionRecordedEvent) for event in events)
    assert not any(isinstance(event, TaskStatusChangedEvent) for event in events)


def test_day_record_task_action_emits_punt_event() -> None:
    user_id = uuid4()
    day = _build_day(user_id)
    task = _build_task(user_id, day.date)
    action = value_objects.Action(type=value_objects.ActionType.PUNT)

    day.record_task_action(task, action)
    events = day.collect_events()

    assert any(isinstance(event, TaskPuntedEvent) for event in events)


def test_day_record_task_action_validates_task() -> None:
    user_id = uuid4()
    day = _build_day(user_id)
    task = _build_task(user_id, dt_date(2025, 11, 28))

    with pytest.raises(DomainError, match="does not match day date"):
        day.record_task_action(task, value_objects.Action(type=value_objects.ActionType.NOTIFY))

    task = _build_task(uuid4(), day.date)
    with pytest.raises(DomainError, match="does not match day user_id"):
        day.record_task_action(task, value_objects.Action(type=value_objects.ActionType.NOTIFY))


def test_day_alarm_lifecycle() -> None:
    user_id = uuid4()
    day = _build_day(user_id)
    alarm = value_objects.Alarm(
        name="Wake up",
        time=time(8, 0),
        datetime=datetime(2025, 11, 27, 8, 0, tzinfo=UTC),
        type=value_objects.AlarmType.GENERIC,
        url="https://example.com",
    )

    added = day.add_alarm(alarm)
    events = day.collect_events()
    assert isinstance(events[0], AlarmAddedEvent)
    assert added == alarm

    removed = day.remove_alarm("Wake up", time(8, 0), alarm_type=alarm.type)
    events = day.collect_events()
    assert any(isinstance(event, AlarmRemovedEvent) for event in events)
    assert removed.id == alarm.id


def test_day_remove_alarm_respects_type_and_url() -> None:
    user_id = uuid4()
    day = _build_day(user_id)
    alarm_a = value_objects.Alarm(
        name="Alarm",
        time=time(8, 0),
        type=value_objects.AlarmType.URL,
        url="https://example.com/a",
    )
    alarm_b = value_objects.Alarm(
        name="Alarm",
        time=time(8, 0),
        type=value_objects.AlarmType.GENERIC,
        url="https://example.com/b",
    )
    day.add_alarm(alarm_a)
    day.add_alarm(alarm_b)
    day.collect_events()

    removed = day.remove_alarm(
        "Alarm",
        time(8, 0),
        alarm_type=value_objects.AlarmType.GENERIC,
        url="https://example.com/b",
    )

    assert removed.id == alarm_b.id


def test_day_remove_alarm_skips_non_matching_name_and_url() -> None:
    user_id = uuid4()
    day = _build_day(user_id)
    alarm_a = value_objects.Alarm(
        name="Alarm A",
        time=time(8, 0),
        type=value_objects.AlarmType.URL,
        url="https://example.com/a",
    )
    alarm_b = value_objects.Alarm(
        name="Alarm B",
        time=time(9, 0),
        type=value_objects.AlarmType.URL,
        url="https://example.com/b",
    )
    alarm_c = value_objects.Alarm(
        name="Alarm B",
        time=time(9, 0),
        type=value_objects.AlarmType.URL,
        url="https://example.com/c",
    )
    day.add_alarm(alarm_a)
    day.add_alarm(alarm_b)
    day.add_alarm(alarm_c)
    day.collect_events()

    removed = day.remove_alarm(
        "Alarm B",
        time(9, 0),
        alarm_type=value_objects.AlarmType.URL,
        url="https://example.com/c",
    )

    assert removed.id == alarm_c.id


def test_day_remove_alarm_raises_when_missing() -> None:
    user_id = uuid4()
    day = _build_day(user_id)

    with pytest.raises(DomainError, match="not found in this day"):
        day.remove_alarm("Missing", time(9, 0))


def test_day_update_alarm_status_emits_events() -> None:
    user_id = uuid4()
    day = _build_day(user_id)
    alarm = value_objects.Alarm(name="Alarm", time=time(9, 0))
    day.add_alarm(alarm)
    day.collect_events()

    updated = day.update_alarm_status(
        alarm.id,
        value_objects.AlarmStatus.SNOOZED,
        snoozed_until=datetime(2025, 11, 27, 9, 15, tzinfo=UTC),
    )
    events = day.collect_events()
    assert isinstance(events[0], AlarmStatusChangedEvent)
    assert updated.snoozed_until is not None

    triggered = day.update_alarm_status(
        alarm.id,
        value_objects.AlarmStatus.TRIGGERED,
    )
    events = day.collect_events()
    assert isinstance(events[0], AlarmTriggeredEvent)
    assert triggered.status == value_objects.AlarmStatus.TRIGGERED


def test_day_update_alarm_status_requires_snooze_until() -> None:
    user_id = uuid4()
    day = _build_day(user_id)
    alarm = value_objects.Alarm(name="Alarm", time=time(9, 0))
    day.add_alarm(alarm)

    with pytest.raises(DomainError, match="Snoozed alarms require snoozed_until"):
        day.update_alarm_status(alarm.id, value_objects.AlarmStatus.SNOOZED)


def test_day_update_alarm_status_raises_when_missing() -> None:
    user_id = uuid4()
    day = _build_day(user_id)

    with pytest.raises(DomainError, match="not found in this day"):
        day.update_alarm_status(uuid4(), value_objects.AlarmStatus.ACTIVE)


def test_day_update_alarm_status_skips_non_matching_alarm() -> None:
    user_id = uuid4()
    day = _build_day(user_id)
    alarm_a = value_objects.Alarm(name="Alarm A", time=time(8, 0))
    alarm_b = value_objects.Alarm(name="Alarm B", time=time(9, 0))
    day.add_alarm(alarm_a)
    day.add_alarm(alarm_b)
    day.collect_events()

    updated = day.update_alarm_status(alarm_b.id, value_objects.AlarmStatus.CANCELLED)

    assert updated.id == alarm_b.id


def test_day_update_alarm_status_noop_returns_alarm() -> None:
    user_id = uuid4()
    day = _build_day(user_id)
    alarm = value_objects.Alarm(name="Alarm", time=time(9, 0))
    day.add_alarm(alarm)
    day.collect_events()

    same = day.update_alarm_status(alarm.id, alarm.status)

    assert same.id == alarm.id
    assert day.collect_events() == []


def test_day_update_reminder_status_skips_non_matching_reminders() -> None:
    user_id = uuid4()
    day = _build_day(user_id)
    reminder_a = day.add_reminder("Reminder A")
    reminder_b = day.add_reminder("Reminder B")
    day.collect_events()

    updated = day.update_reminder_status(
        reminder_b.id, value_objects.ReminderStatus.COMPLETE
    )

    assert updated.id == reminder_b.id
    assert any(reminder.id == reminder_a.id for reminder in day.reminders)
