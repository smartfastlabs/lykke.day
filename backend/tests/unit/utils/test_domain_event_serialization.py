from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from lykke.core.utils.domain_event_serialization import (
    deserialize_domain_event,
    serialize_domain_event,
)
from lykke.domain.events.task_events import TaskCompletedEvent, TaskStateUpdatedEvent


def test_serialize_domain_event_task_completed() -> None:
    user_id = uuid4()
    task_id = uuid4()
    completed_at = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    scheduled_date = date(2025, 1, 1)
    event = TaskCompletedEvent(
        user_id=user_id,
        task_id=task_id,
        completed_at=completed_at,
        task_scheduled_date=scheduled_date,
        task_name="Finish report",
        task_type="WORK",
        task_category="PROFESSIONAL",
    )

    serialized = serialize_domain_event(event)

    assert serialized["event_type"].endswith("TaskCompletedEvent")
    assert serialized["event_data"]["user_id"] == str(user_id)
    assert serialized["event_data"]["task_id"] == str(task_id)
    assert serialized["event_data"]["completed_at"] == completed_at.isoformat()
    assert serialized["event_data"]["task_scheduled_date"] == scheduled_date.isoformat()
    assert serialized["event_data"]["task_name"] == "Finish report"


def test_deserialize_domain_event_round_trip() -> None:
    user_id = uuid4()
    task_id = uuid4()
    completed_at = datetime(2025, 1, 2, 9, 15, tzinfo=UTC)
    scheduled_date = date(2025, 1, 2)
    event = TaskCompletedEvent(
        user_id=user_id,
        task_id=task_id,
        completed_at=completed_at,
        task_scheduled_date=scheduled_date,
        task_name=None,
        task_type=None,
        task_category=None,
    )

    serialized = serialize_domain_event(event)
    deserialized = deserialize_domain_event(serialized)

    assert isinstance(deserialized, TaskCompletedEvent)
    assert deserialized.task_id == task_id
    assert deserialized.completed_at == completed_at
    assert deserialized.task_scheduled_date == scheduled_date
    assert deserialized.task_name is None


def test_deserialize_domain_event_coerces_entity_date() -> None:
    user_id = uuid4()
    task_id = uuid4()
    scheduled_date = date(2025, 1, 3)
    event = TaskStateUpdatedEvent(
        user_id=user_id,
        task_id=task_id,
        action_type="COMPLETE",
        old_status="NOT_STARTED",
        new_status="COMPLETE",
        completed_at=datetime(2025, 1, 3, 12, 0, tzinfo=UTC),
        entity_id=task_id,
        entity_type="task",
        entity_date=scheduled_date,
    )

    serialized = serialize_domain_event(event)
    deserialized = deserialize_domain_event(serialized)

    assert isinstance(deserialized, TaskStateUpdatedEvent)
    assert deserialized.entity_date == scheduled_date


def test_deserialize_domain_event_requires_type_and_data() -> None:
    with pytest.raises(ValueError, match="missing 'event_type' or 'event_data'"):
        deserialize_domain_event({"event_type": "x"})
