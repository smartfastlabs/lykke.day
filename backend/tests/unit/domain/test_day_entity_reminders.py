"""Unit tests for DayEntity reminder methods."""

import datetime
from datetime import UTC
from uuid import uuid4

import pytest
from lykke.core.exceptions import DomainError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity
from lykke.domain.events.day_events import (
    ReminderAddedEvent,
    ReminderRemovedEvent,
    ReminderStatusChangedEvent,
)


@pytest.fixture
def test_day(test_user_id: str) -> DayEntity:
    """Create a test day."""
    template = DayTemplateEntity(
        user_id=test_user_id,
        slug="default",
        routine_definition_ids=[],
        time_blocks=[],
    )
    return DayEntity.create_for_date(
        datetime.date(2025, 11, 27),
        user_id=test_user_id,
        template=template,
    )


def test_add_reminder_adds_reminder_to_day(test_day: DayEntity) -> None:
    """Test add_reminder adds a reminder to the day."""
    reminder = test_day.add_reminder("Test Reminder")

    assert len(test_day.reminders) == 1
    assert test_day.reminders[0].name == "Test Reminder"
    assert test_day.reminders[0].status == value_objects.ReminderStatus.INCOMPLETE
    assert test_day.reminders[0].id == reminder.id
    assert reminder.name == "Test Reminder"


def test_add_reminder_emits_domain_event(test_day: DayEntity) -> None:
    """Test add_reminder emits ReminderAddedEvent."""
    reminder = test_day.add_reminder("Test Reminder")

    events = test_day.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], ReminderAddedEvent)
    assert events[0].reminder_id == reminder.id
    assert events[0].reminder_name == "Test Reminder"
    assert events[0].day_id == test_day.id
    assert events[0].date == test_day.date


def test_add_reminder_sets_created_at(test_day: DayEntity) -> None:
    """Test add_reminder sets created_at timestamp."""
    reminder = test_day.add_reminder("Test Reminder")

    assert reminder.created_at is not None
    assert reminder.created_at.tzinfo == UTC


def test_update_reminder_status_updates_status(test_day: DayEntity) -> None:
    """Test update_reminder_status updates the reminder's status."""
    reminder = test_day.add_reminder("Test Reminder")
    reminder_id = reminder.id

    test_day.update_reminder_status(reminder_id, value_objects.ReminderStatus.COMPLETE)

    updated_reminder = next(g for g in test_day.reminders if g.id == reminder_id)
    assert updated_reminder.status == value_objects.ReminderStatus.COMPLETE
    assert updated_reminder.name == "Test Reminder"  # Name unchanged


def test_update_reminder_status_emits_domain_event(test_day: DayEntity) -> None:
    """Test update_reminder_status emits ReminderStatusChangedEvent."""
    reminder = test_day.add_reminder("Test Reminder")
    # Clear events from add_reminder
    test_day.collect_events()

    test_day.update_reminder_status(reminder.id, value_objects.ReminderStatus.COMPLETE)

    events = test_day.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], ReminderStatusChangedEvent)
    assert events[0].reminder_id == reminder.id
    assert events[0].reminder_name == "Test Reminder"
    assert events[0].old_status == value_objects.ReminderStatus.INCOMPLETE
    assert events[0].new_status == value_objects.ReminderStatus.COMPLETE
    assert events[0].day_id == test_day.id
    assert events[0].date == test_day.date


def test_update_reminder_status_raises_error_if_reminder_not_found(
    test_day: DayEntity,
) -> None:
    """Test update_reminder_status raises error if reminder doesn't exist."""
    fake_reminder_id = uuid4()

    with pytest.raises(DomainError, match="not found"):
        test_day.update_reminder_status(
            fake_reminder_id, value_objects.ReminderStatus.COMPLETE
        )


def test_update_reminder_status_no_change_if_same_status(test_day: DayEntity) -> None:
    """Test update_reminder_status doesn't emit event if status unchanged."""
    reminder = test_day.add_reminder("Test Reminder")
    # Clear events from add_reminder
    test_day.collect_events()

    test_day.update_reminder_status(
        reminder.id, value_objects.ReminderStatus.INCOMPLETE
    )

    # No event should be emitted for no-op status change
    events = test_day.collect_events()
    assert len(events) == 0


def test_update_reminder_status_all_transitions(test_day: DayEntity) -> None:
    """Test update_reminder_status works for all status transitions."""
    reminder = test_day.add_reminder("Test Reminder")

    # INCOMPLETE -> COMPLETE
    test_day.update_reminder_status(reminder.id, value_objects.ReminderStatus.COMPLETE)
    assert test_day.reminders[0].status == value_objects.ReminderStatus.COMPLETE

    # COMPLETE -> PUNT
    test_day.update_reminder_status(reminder.id, value_objects.ReminderStatus.PUNT)
    assert test_day.reminders[0].status == value_objects.ReminderStatus.PUNT

    # PUNT -> INCOMPLETE
    test_day.update_reminder_status(
        reminder.id, value_objects.ReminderStatus.INCOMPLETE
    )
    assert test_day.reminders[0].status == value_objects.ReminderStatus.INCOMPLETE


def test_remove_reminder_removes_reminder_from_day(test_day: DayEntity) -> None:
    """Test remove_reminder removes the reminder from the day."""
    reminder1 = test_day.add_reminder("Reminder 1")
    reminder2 = test_day.add_reminder("Reminder 2")

    test_day.remove_reminder(reminder1.id)

    assert len(test_day.reminders) == 1
    assert test_day.reminders[0].id == reminder2.id
    assert test_day.reminders[0].name == "Reminder 2"


def test_remove_reminder_emits_domain_event(test_day: DayEntity) -> None:
    """Test remove_reminder emits ReminderRemovedEvent."""
    reminder = test_day.add_reminder("Test Reminder")
    # Clear events from add_reminder
    test_day.collect_events()

    test_day.remove_reminder(reminder.id)

    events = test_day.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], ReminderRemovedEvent)
    assert events[0].reminder_id == reminder.id
    assert events[0].reminder_name == "Test Reminder"
    assert events[0].day_id == test_day.id
    assert events[0].date == test_day.date


def test_remove_reminder_raises_error_if_reminder_not_found(
    test_day: DayEntity,
) -> None:
    """Test remove_reminder raises error if reminder doesn't exist."""
    fake_reminder_id = uuid4()

    with pytest.raises(DomainError, match="not found"):
        test_day.remove_reminder(fake_reminder_id)


def test_remove_reminder_with_multiple_reminders(test_day: DayEntity) -> None:
    """Test remove_reminder works correctly with multiple reminders."""
    reminder1 = test_day.add_reminder("Reminder 1")
    reminder2 = test_day.add_reminder("Reminder 2")
    reminder3 = test_day.add_reminder("Reminder 3")

    # Remove middle reminder
    test_day.remove_reminder(reminder2.id)

    assert len(test_day.reminders) == 2
    assert test_day.reminders[0].id == reminder1.id
    assert test_day.reminders[1].id == reminder3.id
