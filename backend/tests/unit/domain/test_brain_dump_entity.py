"""Unit tests for BrainDumpEntity domain methods."""

from datetime import date
from uuid import uuid4

from lykke.domain import value_objects
from lykke.domain.entities import BrainDumpEntity, DayEntity
from lykke.domain.events.day_events import (
    BrainDumpAddedEvent,
    BrainDumpRemovedEvent,
    BrainDumpStatusChangedEvent,
    BrainDumpTypeChangedEvent,
)


def test_mark_added_emits_event() -> None:
    user_id = uuid4()
    day_date = date(2025, 11, 27)
    item = BrainDumpEntity(user_id=user_id, date=day_date, text="Remember to call")

    item.mark_added()
    events = item.collect_events()

    assert len(events) == 1
    assert isinstance(events[0], BrainDumpAddedEvent)
    assert events[0].item_id == item.id
    assert events[0].item_text == item.text
    assert events[0].day_id == DayEntity.id_from_date_and_user(day_date, user_id)
    assert events[0].date == day_date


def test_update_status_emits_event() -> None:
    user_id = uuid4()
    day_date = date(2025, 11, 27)
    item = BrainDumpEntity(user_id=user_id, date=day_date, text="Pick up coffee")

    updated = item.update_status(value_objects.BrainDumpStatus.COMPLETE)
    events = updated.collect_events()

    assert updated.status == value_objects.BrainDumpStatus.COMPLETE
    assert len(events) == 1
    assert isinstance(events[0], BrainDumpStatusChangedEvent)
    assert events[0].old_status == value_objects.BrainDumpStatus.ACTIVE
    assert events[0].new_status == value_objects.BrainDumpStatus.COMPLETE
    assert events[0].item_text == item.text


def test_update_status_no_change_no_event() -> None:
    item = BrainDumpEntity(
        user_id=uuid4(),
        date=date(2025, 11, 27),
        text="Refill filters",
    )

    updated = item.update_status(value_objects.BrainDumpStatus.ACTIVE)
    events = updated.collect_events()

    assert updated.status == value_objects.BrainDumpStatus.ACTIVE
    assert len(events) == 0


def test_update_type_emits_event() -> None:
    item = BrainDumpEntity(
        user_id=uuid4(),
        date=date(2025, 11, 27),
        text="Capture action",
    )

    updated = item.update_type(value_objects.BrainDumpType.COMMAND)
    events = updated.collect_events()

    assert updated.type == value_objects.BrainDumpType.COMMAND
    assert len(events) == 1
    assert isinstance(events[0], BrainDumpTypeChangedEvent)
    assert events[0].old_type == value_objects.BrainDumpType.GENERAL
    assert events[0].new_type == value_objects.BrainDumpType.COMMAND


def test_mark_removed_emits_event() -> None:
    item = BrainDumpEntity(
        user_id=uuid4(),
        date=date(2025, 11, 27),
        text="Call mom",
    )

    item.mark_removed()
    events = item.collect_events()

    assert len(events) == 1
    assert isinstance(events[0], BrainDumpRemovedEvent)
    assert events[0].item_id == item.id
    assert events[0].item_text == item.text
