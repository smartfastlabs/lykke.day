"""Unit tests for RemoveReminderHandler."""

import datetime
from datetime import UTC, date as dt_date
from uuid import uuid4

import pytest

from lykke.application.commands.day import RemoveReminderCommand, RemoveReminderHandler
from lykke.core.exceptions import DomainError, NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity
from lykke.domain.events.day_events import ReminderRemovedEvent
from tests.unit.fakes import (
    _FakeDayReadOnlyRepo,
    _FakeReadOnlyRepos,
    _FakeUoW,
    _FakeUoWFactory,
)


@pytest.mark.asyncio
async def test_remove_reminder_removes_reminder_from_day():
    """Test remove_reminder removes the reminder from the day."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    reminder1 = day.add_reminder("Reminder 1")
    reminder2 = day.add_reminder("Reminder 2")
    # Clear events from add_reminder
    day.collect_events()

    day_repo = _FakeDayReadOnlyRepo(day)
    ro_repos = _FakeReadOnlyRepos(day_repo=day_repo)
    uow = _FakeUoW(day_repo=day_repo)
    uow_factory = _FakeUoWFactory(uow)
    handler = RemoveReminderHandler(ro_repos, uow_factory, user_id)

    # Act
    result = await handler.handle(RemoveReminderCommand(date=task_date, reminder_id=reminder1.id))

    # Assert
    assert len(result.reminders) == 1
    assert result.reminders[0].id == reminder2.id
    assert result.reminders[0].name == "Reminder 2"
    assert len(uow_factory.uow.added) == 1
    assert uow_factory.uow.added[0] == result


@pytest.mark.asyncio
async def test_remove_reminder_emits_domain_event():
    """Test remove_reminder emits ReminderRemovedEvent."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    reminder = day.add_reminder("Test Reminder")
    # Clear events from add_reminder
    day.collect_events()

    day_repo = _FakeDayReadOnlyRepo(day)
    ro_repos = _FakeReadOnlyRepos(day_repo=day_repo)
    uow = _FakeUoW(day_repo=day_repo)
    uow_factory = _FakeUoWFactory(uow)
    handler = RemoveReminderHandler(ro_repos, uow_factory, user_id)

    # Act
    result = await handler.handle(RemoveReminderCommand(date=task_date, reminder_id=reminder.id))

    # Assert
    events = result.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], ReminderRemovedEvent)
    assert events[0].reminder_id == reminder.id
    assert events[0].reminder_name == "Test Reminder"
    assert events[0].day_id == day.id
    assert events[0].date == task_date


@pytest.mark.asyncio
async def test_remove_reminder_raises_error_if_reminder_not_found():
    """Test remove_reminder raises error if reminder doesn't exist."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    fake_reminder_id = uuid4()

    day_repo = _FakeDayReadOnlyRepo(day)
    ro_repos = _FakeReadOnlyRepos(day_repo=day_repo)
    uow = _FakeUoW(day_repo=day_repo)
    uow_factory = _FakeUoWFactory(uow)
    handler = RemoveReminderHandler(ro_repos, uow_factory, user_id)

    # Act & Assert
    with pytest.raises(DomainError, match="not found"):
        await handler.handle(RemoveReminderCommand(date=task_date, reminder_id=fake_reminder_id))


@pytest.mark.asyncio
async def test_remove_reminder_with_multiple_reminders():
    """Test remove_reminder works correctly with multiple reminders."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    reminder1 = day.add_reminder("Reminder 1")
    reminder2 = day.add_reminder("Reminder 2")
    reminder3 = day.add_reminder("Reminder 3")

    day_repo = _FakeDayReadOnlyRepo(day)
    ro_repos = _FakeReadOnlyRepos(day_repo=day_repo)
    uow = _FakeUoW(day_repo=day_repo)
    uow_factory = _FakeUoWFactory(uow)
    handler = RemoveReminderHandler(ro_repos, uow_factory, user_id)

    # Remove middle reminder
    result = await handler.handle(RemoveReminderCommand(date=task_date, reminder_id=reminder2.id))

    # Assert
    assert len(result.reminders) == 2
    assert result.reminders[0].id == reminder1.id
    assert result.reminders[1].id == reminder3.id
