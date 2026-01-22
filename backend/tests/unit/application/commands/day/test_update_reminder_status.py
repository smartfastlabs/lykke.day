"""Unit tests for UpdateReminderStatusHandler."""

from datetime import date as dt_date
from uuid import uuid4

import pytest

from lykke.application.commands.day import UpdateReminderStatusCommand, UpdateReminderStatusHandler
from lykke.core.exceptions import DomainError, NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity
from lykke.domain.events.day_events import ReminderStatusChangedEvent


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
        self.time_block_definition_ro_repo = fake
        self.usecase_config_ro_repo = fake
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
async def test_update_reminder_status_updates_status():
    """Test update_reminder_status updates the reminder's status."""
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
    handler = UpdateReminderStatusHandler(ro_repos, uow_factory, user_id)

    # Act
    result = await handler.handle(
        UpdateReminderStatusCommand(
            date=task_date,
            reminder_id=reminder.id,
            status=value_objects.ReminderStatus.COMPLETE,
        )
    )

    # Assert
    updated_reminder = next(r for r in result.reminders if r.id == reminder.id)
    assert updated_reminder.status == value_objects.ReminderStatus.COMPLETE
    assert len(uow_factory.uow.added) == 1
    assert uow_factory.uow.added[0] == result


@pytest.mark.asyncio
async def test_update_reminder_status_emits_domain_event():
    """Test update_reminder_status emits ReminderStatusChangedEvent."""
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
    handler = UpdateReminderStatusHandler(ro_repos, uow_factory, user_id)

    # Act
    result = await handler.handle(
        UpdateReminderStatusCommand(
            date=task_date,
            reminder_id=reminder.id,
            status=value_objects.ReminderStatus.COMPLETE,
        )
    )

    # Assert
    events = result.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], ReminderStatusChangedEvent)
    assert events[0].reminder_id == reminder.id
    assert events[0].reminder_name == "Test Reminder"
    assert events[0].old_status == value_objects.ReminderStatus.INCOMPLETE
    assert events[0].new_status == value_objects.ReminderStatus.COMPLETE
    assert events[0].day_id == day.id


@pytest.mark.asyncio
async def test_update_reminder_status_raises_error_if_reminder_not_found():
    """Test update_reminder_status raises error if reminder doesn't exist."""
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
    handler = UpdateReminderStatusHandler(ro_repos, uow_factory, user_id)

    # Act & Assert
    with pytest.raises(DomainError, match="not found"):
        await handler.handle(
            UpdateReminderStatusCommand(
                date=task_date,
                reminder_id=fake_reminder_id,
                status=value_objects.ReminderStatus.COMPLETE,
            )
        )


@pytest.mark.asyncio
async def test_update_reminder_status_no_change_does_not_add_to_uow():
    """Test update_reminder_status doesn't add entity to UoW if status unchanged."""
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
    
    # Set reminder status to COMPLETE
    day.update_reminder_status(reminder.id, value_objects.ReminderStatus.COMPLETE)
    # Clear events from update
    day.collect_events()

    day_repo = _FakeDayReadOnlyRepo(day)
    ro_repos = _FakeReadOnlyRepos(day_repo)
    uow_factory = _FakeUoWFactory(day_repo)
    handler = UpdateReminderStatusHandler(ro_repos, uow_factory, user_id)

    # Act - try to update to same status
    result = await handler.handle(
        UpdateReminderStatusCommand(
            date=task_date,
            reminder_id=reminder.id,
            status=value_objects.ReminderStatus.COMPLETE,
        )
    )

    # Assert - entity should not be added to UoW because status didn't change
    assert len(uow_factory.uow.added) == 0
    assert result.reminders[0].status == value_objects.ReminderStatus.COMPLETE
    # No events should be emitted
    events = result.collect_events()
    assert len(events) == 0


@pytest.mark.asyncio
async def test_update_reminder_status_all_status_transitions():
    """Test update_reminder_status works for all status transitions."""
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

    day_repo = _FakeDayReadOnlyRepo(day)
    ro_repos = _FakeReadOnlyRepos(day_repo)
    uow_factory = _FakeUoWFactory(day_repo)
    handler = UpdateReminderStatusHandler(ro_repos, uow_factory, user_id)

    # INCOMPLETE -> COMPLETE
    result = await handler.handle(
        UpdateReminderStatusCommand(
            date=task_date,
            reminder_id=reminder.id,
            status=value_objects.ReminderStatus.COMPLETE,
        )
    )
    assert result.reminders[0].status == value_objects.ReminderStatus.COMPLETE

    # Update the day in repo for next test
    day_repo._day = result

    # COMPLETE -> PUNT
    result = await handler.handle(
        UpdateReminderStatusCommand(
            date=task_date,
            reminder_id=reminder.id,
            status=value_objects.ReminderStatus.PUNT,
        )
    )
    assert result.reminders[0].status == value_objects.ReminderStatus.PUNT

    # Update the day in repo for next test
    day_repo._day = result

    # PUNT -> INCOMPLETE
    result = await handler.handle(
        UpdateReminderStatusCommand(
            date=task_date,
            reminder_id=reminder.id,
            status=value_objects.ReminderStatus.INCOMPLETE,
        )
    )
    assert result.reminders[0].status == value_objects.ReminderStatus.INCOMPLETE
