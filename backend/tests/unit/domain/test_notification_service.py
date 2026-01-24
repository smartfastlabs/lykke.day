"""Unit tests for notification domain service."""

import datetime
from datetime import UTC
from uuid import uuid4

import pytest

from lykke.application.notifications import (
    build_notification_payload_for_calendar_entries,
    build_notification_payload_for_calendar_entry_change,
    build_notification_payload_for_tasks,
)
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntity, CalendarEntryEntity, TaskEntity


@pytest.fixture
def test_task(test_user_id: str) -> TaskEntity:
    """Create a test task."""
    return TaskEntity(
        user_id=test_user_id,
        scheduled_date=datetime.date(2025, 11, 27),
        name="Test Task",
        status=value_objects.TaskStatus.READY,
        type=value_objects.TaskType.CHORE,
        description="Test description",
        category=value_objects.TaskCategory.HYGIENE,
        frequency=value_objects.TaskFrequency.DAILY,
    )


def test_build_for_tasks_single_task(test_task: TaskEntity) -> None:
    """Test building notification payload for a single task."""
    payload = build_notification_payload_for_tasks([test_task])

    assert payload.title == "Test Task"
    assert payload.body == "Task ready: Test Task"
    assert len(payload.actions) == 1
    assert payload.actions[0].action == "view"
    assert payload.actions[0].title == "View Tasks"
    assert payload.data["type"] == "tasks"
    assert len(payload.data["task_ids"]) == 1
    assert str(test_task.id) in payload.data["task_ids"]
    assert len(payload.data["tasks"]) == 1
    assert payload.data["tasks"][0]["name"] == "Test Task"


def test_build_for_tasks_multiple_tasks(test_user_id: str) -> None:
    """Test building notification payload for multiple tasks."""
    task1 = TaskEntity(
        user_id=test_user_id,
        scheduled_date=datetime.date(2025, 11, 27),
        name="Task 1",
        status=value_objects.TaskStatus.READY,
        type=value_objects.TaskType.CHORE,
        description="Test description",
        category=value_objects.TaskCategory.HYGIENE,
        frequency=value_objects.TaskFrequency.DAILY,
    )
    task2 = TaskEntity(
        user_id=test_user_id,
        scheduled_date=datetime.date(2025, 11, 27),
        name="Task 2",
        status=value_objects.TaskStatus.READY,
        type=value_objects.TaskType.CHORE,
        description="Test description",
        category=value_objects.TaskCategory.HYGIENE,
        frequency=value_objects.TaskFrequency.DAILY,
    )

    payload = build_notification_payload_for_tasks([task1, task2])

    assert payload.title == "2 tasks ready"
    assert payload.body == "You have 2 tasks ready"
    assert len(payload.data["task_ids"]) == 2
    assert len(payload.data["tasks"]) == 2


def test_build_for_calendar_entries_single(test_user_id: str) -> None:
    """Test building notification payload for a single calendar entry."""

    calendar = CalendarEntity(
        user_id=test_user_id,
        name="Test Calendar",
        platform="google",
        platform_id="cal123",
        auth_token_id=uuid4(),
    )
    entry = CalendarEntryEntity(
        user_id=test_user_id,
        calendar_id=calendar.id,
        name="Test Event",
        starts_at=datetime.datetime(2025, 11, 27, 12, 0, 0, tzinfo=UTC),
        ends_at=datetime.datetime(2025, 11, 27, 13, 0, 0, tzinfo=UTC),
        platform_id="event123",
        platform="google",
        status="confirmed",
        frequency=value_objects.TaskFrequency.ONCE,
    )

    payload = build_notification_payload_for_calendar_entries([entry])

    assert payload.title == "Test Event"
    assert payload.body == "Event starting soon: Test Event"
    assert len(payload.actions) == 1
    assert payload.actions[0].action == "view"
    assert payload.actions[0].title == "View Events"
    assert payload.data["type"] == "calendar_entries"
    assert len(payload.data["calendar_entry_ids"]) == 1
    assert str(entry.id) in payload.data["calendar_entry_ids"]


def test_build_for_calendar_entries_multiple(test_user_id: str) -> None:
    """Test building notification payload for multiple calendar entries."""

    calendar = CalendarEntity(
        user_id=test_user_id,
        name="Test Calendar",
        platform="google",
        platform_id="cal123",
        auth_token_id=uuid4(),
    )
    entry1 = CalendarEntryEntity(
        user_id=test_user_id,
        calendar_id=calendar.id,
        name="Event 1",
        starts_at=datetime.datetime(2025, 11, 27, 12, 0, 0, tzinfo=UTC),
        ends_at=datetime.datetime(2025, 11, 27, 13, 0, 0, tzinfo=UTC),
        platform_id="event1",
        platform="google",
        status="confirmed",
        frequency=value_objects.TaskFrequency.ONCE,
    )
    entry2 = CalendarEntryEntity(
        user_id=test_user_id,
        calendar_id=calendar.id,
        name="Event 2",
        starts_at=datetime.datetime(2025, 11, 27, 14, 0, 0, tzinfo=UTC),
        ends_at=datetime.datetime(2025, 11, 27, 15, 0, 0, tzinfo=UTC),
        platform_id="event2",
        platform="google",
        status="confirmed",
        frequency=value_objects.TaskFrequency.ONCE,
    )

    payload = build_notification_payload_for_calendar_entries([entry1, entry2])

    assert payload.title == "2 events starting soon"
    assert payload.body == "You have 2 events starting soon"
    assert len(payload.data["calendar_entry_ids"]) == 2
    assert len(payload.data["calendar_entries"]) == 2


def test_build_for_calendar_entries_no_ends_at(test_user_id: str) -> None:
    """Test building notification payload for calendar entry without ends_at."""

    calendar = CalendarEntity(
        user_id=test_user_id,
        name="Test Calendar",
        platform="google",
        platform_id="cal123",
        auth_token_id=uuid4(),
    )
    entry = CalendarEntryEntity(
        user_id=test_user_id,
        calendar_id=calendar.id,
        name="All Day Event",
        starts_at=datetime.datetime(2025, 11, 27, 12, 0, 0, tzinfo=UTC),
        ends_at=None,
        platform_id="event123",
        platform="google",
        status="confirmed",
        frequency=value_objects.TaskFrequency.ONCE,
    )

    payload = build_notification_payload_for_calendar_entries([entry])

    assert payload.data["calendar_entries"][0]["ends_at"] is None


def test_build_for_calendar_entry_change_created(test_user_id: str) -> None:
    """Test building notification payload for calendar entry created event."""

    calendar = CalendarEntity(
        user_id=test_user_id,
        name="Test Calendar",
        platform="google",
        platform_id="cal123",
        auth_token_id=uuid4(),
    )
    entry = CalendarEntryEntity(
        user_id=test_user_id,
        calendar_id=calendar.id,
        name="Test Event",
        starts_at=datetime.datetime(2025, 11, 27, 12, 0, 0, tzinfo=UTC),
        ends_at=datetime.datetime(2025, 11, 27, 13, 0, 0, tzinfo=UTC),
        platform_id="event123",
        platform="google",
        status="confirmed",
        frequency=value_objects.TaskFrequency.ONCE,
    )

    payload = build_notification_payload_for_calendar_entry_change("created", entry)

    assert payload.title == "Calendar event created"
    assert payload.body == "Test Event"
    assert payload.data["change_type"] == "created"
    assert payload.data["calendar_entry_id"] == str(entry.id)
    assert payload.data["calendar_entry"]["name"] == "Test Event"


def test_build_for_calendar_entry_change_edited(test_user_id: str) -> None:
    """Test building notification payload for calendar entry edited event."""

    calendar = CalendarEntity(
        user_id=test_user_id,
        name="Test Calendar",
        platform="google",
        platform_id="cal123",
        auth_token_id=uuid4(),
    )
    entry = CalendarEntryEntity(
        user_id=test_user_id,
        calendar_id=calendar.id,
        name="Updated Event",
        starts_at=datetime.datetime(2025, 11, 27, 14, 0, 0, tzinfo=UTC),
        ends_at=datetime.datetime(2025, 11, 27, 15, 0, 0, tzinfo=UTC),
        platform_id="event123",
        platform="google",
        status="confirmed",
        frequency=value_objects.TaskFrequency.ONCE,
    )

    payload = build_notification_payload_for_calendar_entry_change("edited", entry)

    assert payload.title == "Calendar event edited"
    assert payload.body == "Updated Event"
    assert payload.data["change_type"] == "edited"
    assert payload.data["calendar_entry_id"] == str(entry.id)


def test_build_for_calendar_entry_change_deleted(test_user_id: str) -> None:
    """Test building notification payload for calendar entry deleted event."""

    entry_snapshot = {
        "id": str(uuid4()),
        "name": "Deleted Event",
        "starts_at": "2025-11-27T12:00:00+00:00",
        "ends_at": "2025-11-27T13:00:00+00:00",
        "calendar_id": str(uuid4()),
        "platform_id": "event123",
        "status": "confirmed",
    }

    payload = build_notification_payload_for_calendar_entry_change(
        "deleted", entry_snapshot
    )

    assert payload.title == "Calendar event deleted"
    assert payload.body == "Deleted Event"
    assert payload.data["change_type"] == "deleted"
    assert payload.data["calendar_entry_id"] == entry_snapshot["id"]
    assert payload.data["calendar_entry"]["name"] == "Deleted Event"
