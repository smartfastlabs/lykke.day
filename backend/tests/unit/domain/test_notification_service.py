"""Unit tests for notification domain service."""

import datetime
from datetime import UTC
from uuid import uuid4

import pytest

from lykke.core.utils import (
    build_notification_payload_for_calendar_entries,
    build_notification_payload_for_tasks,
)
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntity, CalendarEntryEntity, TaskEntity
from lykke.infrastructure import data_objects


@pytest.fixture
def test_task(test_user_id: str) -> TaskEntity:
    """Create a test task."""
    task_def = data_objects.TaskDefinition(
        user_id=test_user_id,
        name="Test Task Definition",
        description="Test description",
        type=value_objects.TaskType.CHORE,
    )
    return TaskEntity(
        user_id=test_user_id,
        scheduled_date=datetime.date(2025, 11, 27),
        name="Test Task",
        status=value_objects.TaskStatus.READY,
        task_definition=task_def,
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
    task_def = data_objects.TaskDefinition(
        user_id=test_user_id,
        name="Task Definition",
        description="Test description",
        type=value_objects.TaskType.CHORE,
    )
    task1 = TaskEntity(
        user_id=test_user_id,
        scheduled_date=datetime.date(2025, 11, 27),
        name="Task 1",
        status=value_objects.TaskStatus.READY,
        task_definition=task_def,
        category=value_objects.TaskCategory.HYGIENE,
        frequency=value_objects.TaskFrequency.DAILY,
    )
    task2 = TaskEntity(
        user_id=test_user_id,
        scheduled_date=datetime.date(2025, 11, 27),
        name="Task 2",
        status=value_objects.TaskStatus.READY,
        task_definition=task_def,
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
    from uuid import uuid4
    
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
    from uuid import uuid4
    
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

    payload = build_notification_payload_for_calendar_entries(
        [entry1, entry2]
    )

    assert payload.title == "2 events starting soon"
    assert payload.body == "You have 2 events starting soon"
    assert len(payload.data["calendar_entry_ids"]) == 2
    assert len(payload.data["calendar_entries"]) == 2


def test_build_for_calendar_entries_no_ends_at(test_user_id: str) -> None:
    """Test building notification payload for calendar entry without ends_at."""
    from uuid import uuid4
    
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

