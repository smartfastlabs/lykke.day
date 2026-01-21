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


class _FakeDayReadOnlyRepo:
    """Fake day repository for testing."""

    def __init__(self, day: DayEntity) -> None:
        self._day = day

    async def get(self, day_id):
        if day_id == self._day.id:
            return self._day
        raise NotFoundError(f"Day {day_id} not found")


class _FakeReadOnlyRepos:
    """Lightweight container matching ReadOnlyRepositories protocol."""

    def __init__(self, day_repo: _FakeDayReadOnlyRepo) -> None:
        fake = object()
        self.audit_log_ro_repo = fake
        self.auth_token_ro_repo = fake
        self.bot_personality_ro_repo = fake
        self.calendar_entry_ro_repo = fake
        self.calendar_entry_series_ro_repo = fake
        self.calendar_ro_repo = fake
        self.conversation_ro_repo = fake
        self.day_ro_repo = day_repo
        self.day_template_ro_repo = fake
        self.factoid_ro_repo = fake
        self.message_ro_repo = fake
        self.notification_ro_repo = fake
        self.push_notification_ro_repo = fake
        self.push_subscription_ro_repo = fake
        self.routine_ro_repo = fake
        self.task_definition_ro_repo = fake
        self.task_ro_repo = fake
        self.template_ro_repo = fake
        self.time_block_definition_ro_repo = fake
        self.user_ro_repo = fake


class _FakeUoW:
    """Minimal UnitOfWork that just collects added entities."""

    def __init__(self, day_repo) -> None:
        self.added = []
        self.day_ro_repo = day_repo

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    def add(self, entity):
        self.added.append(entity)
        return entity


class _FakeUoWFactory:
    def __init__(self, day_repo) -> None:
        self.uow = _FakeUoW(day_repo)

    def create(self, _user_id):
        return self.uow


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
    ro_repos = _FakeReadOnlyRepos(day_repo)
    uow_factory = _FakeUoWFactory(day_repo)
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
    ro_repos = _FakeReadOnlyRepos(day_repo)
    uow_factory = _FakeUoWFactory(day_repo)
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
    ro_repos = _FakeReadOnlyRepos(day_repo)
    uow_factory = _FakeUoWFactory(day_repo)
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
    ro_repos = _FakeReadOnlyRepos(day_repo)
    uow_factory = _FakeUoWFactory(day_repo)
    handler = RemoveReminderHandler(ro_repos, uow_factory, user_id)

    # Remove middle reminder
    result = await handler.handle(RemoveReminderCommand(date=task_date, reminder_id=reminder2.id))

    # Assert
    assert len(result.reminders) == 2
    assert result.reminders[0].id == reminder1.id
    assert result.reminders[1].id == reminder3.id
