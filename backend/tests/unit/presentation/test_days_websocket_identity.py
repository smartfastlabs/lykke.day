"""Unit tests for day WebSocket event identity inference."""

# pylint: disable=import-error

from datetime import date as dt_date, time as dt_time
from uuid import uuid4

from lykke.domain.events.day_events import AlarmTriggeredEvent
from lykke.domain.value_objects.day import AlarmType


def test_infer_entity_identity_from_alarm_triggered_event() -> None:
    """AlarmTriggeredEvent should infer day identity for day context updates."""
    user_id = uuid4()
    day_id = uuid4()
    alarm_id = uuid4()
    event_date = dt_date(2025, 1, 31)

    event = AlarmTriggeredEvent(
        user_id=user_id,
        day_id=day_id,
        date=event_date,
        alarm_id=alarm_id,
        alarm_name="Morning Alarm",
        alarm_time=dt_time(8, 0),
        alarm_type=AlarmType.URL,
        alarm_url="https://example.com",
    )

    assert event.entity_id == day_id
    assert event.entity_type == "day"
    assert event.entity_date == event_date
