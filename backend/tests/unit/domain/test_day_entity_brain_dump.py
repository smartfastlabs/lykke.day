"""Unit tests for DayEntity brain dump methods."""

import datetime
from datetime import UTC
from uuid import uuid4

import pytest

from lykke.core.exceptions import DomainError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity
from lykke.domain.events.day_events import (
    BrainDumpItemAddedEvent,
    BrainDumpItemRemovedEvent,
    BrainDumpItemStatusChangedEvent,
)


@pytest.fixture
def test_day(test_user_id: str) -> DayEntity:
    """Create a test day."""
    template = DayTemplateEntity(
        user_id=test_user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )
    return DayEntity.create_for_date(
        datetime.date(2025, 11, 27),
        user_id=test_user_id,
        template=template,
    )


def test_add_brain_dump_item_adds_item(test_day: DayEntity) -> None:
    """Test add_brain_dump_item adds an item to the day."""
    item = test_day.add_brain_dump_item("Remember to get bread")

    assert len(test_day.brain_dump_items) == 1
    assert test_day.brain_dump_items[0].text == "Remember to get bread"
    assert (
        test_day.brain_dump_items[0].status == value_objects.BrainDumpItemStatus.ACTIVE
    )
    assert item.id == test_day.brain_dump_items[0].id


def test_add_brain_dump_item_emits_domain_event(test_day: DayEntity) -> None:
    """Test add_brain_dump_item emits BrainDumpItemAddedEvent."""
    item = test_day.add_brain_dump_item("Idea about strategy XYZ")

    events = test_day.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], BrainDumpItemAddedEvent)
    assert events[0].item_id == item.id
    assert events[0].item_text == item.text
    assert events[0].day_id == test_day.id
    assert events[0].user_id == test_day.user_id
    assert events[0].date == test_day.date


def test_add_brain_dump_item_sets_created_at(test_day: DayEntity) -> None:
    """Test add_brain_dump_item sets created_at timestamp."""
    item = test_day.add_brain_dump_item("Coffee is out")

    assert item.created_at is not None
    assert item.created_at.tzinfo == UTC


def test_update_brain_dump_item_status_updates_status(test_day: DayEntity) -> None:
    """Test update_brain_dump_item_status updates status."""
    item = test_day.add_brain_dump_item("Finish XYZ")
    item_id = item.id

    test_day.update_brain_dump_item_status(
        item_id, value_objects.BrainDumpItemStatus.COMPLETE
    )

    updated_item = next(i for i in test_day.brain_dump_items if i.id == item_id)
    assert updated_item.status == value_objects.BrainDumpItemStatus.COMPLETE


def test_update_brain_dump_item_status_emits_event(test_day: DayEntity) -> None:
    """Test update_brain_dump_item_status emits event."""
    item = test_day.add_brain_dump_item("Pick up coffee")
    test_day.collect_events()

    test_day.update_brain_dump_item_status(
        item.id, value_objects.BrainDumpItemStatus.PUNT
    )

    events = test_day.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], BrainDumpItemStatusChangedEvent)
    assert events[0].item_id == item.id
    assert events[0].item_text == item.text
    assert events[0].old_status == value_objects.BrainDumpItemStatus.ACTIVE
    assert events[0].new_status == value_objects.BrainDumpItemStatus.PUNT


def test_update_brain_dump_item_status_no_change(test_day: DayEntity) -> None:
    """Test update_brain_dump_item_status no-ops on same status."""
    item = test_day.add_brain_dump_item("Refill filters")
    test_day.collect_events()

    test_day.update_brain_dump_item_status(
        item.id, value_objects.BrainDumpItemStatus.ACTIVE
    )

    events = test_day.collect_events()
    assert len(events) == 0


def test_update_brain_dump_item_status_raises_error(test_day: DayEntity) -> None:
    """Test update_brain_dump_item_status raises error if item not found."""
    fake_item_id = uuid4()

    with pytest.raises(DomainError, match="Brain dump item"):
        test_day.update_brain_dump_item_status(
            fake_item_id, value_objects.BrainDumpItemStatus.COMPLETE
        )


def test_remove_brain_dump_item_removes_item(test_day: DayEntity) -> None:
    """Test remove_brain_dump_item removes the item from the day."""
    item1 = test_day.add_brain_dump_item("Brain dump 1")
    item2 = test_day.add_brain_dump_item("Brain dump 2")

    test_day.remove_brain_dump_item(item1.id)

    assert len(test_day.brain_dump_items) == 1
    assert test_day.brain_dump_items[0].id == item2.id


def test_remove_brain_dump_item_emits_event(test_day: DayEntity) -> None:
    """Test remove_brain_dump_item emits BrainDumpItemRemovedEvent."""
    item = test_day.add_brain_dump_item("Call mom")
    test_day.collect_events()

    test_day.remove_brain_dump_item(item.id)

    events = test_day.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], BrainDumpItemRemovedEvent)
    assert events[0].item_id == item.id
    assert events[0].item_text == item.text


def test_remove_brain_dump_item_raises_error(test_day: DayEntity) -> None:
    """Test remove_brain_dump_item raises error if item not found."""
    fake_item_id = uuid4()

    with pytest.raises(DomainError, match="Brain dump item"):
        test_day.remove_brain_dump_item(fake_item_id)
