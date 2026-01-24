"""Unit tests for UpdateReminderStatusHandler."""

from datetime import date as dt_date
from uuid import uuid4

import pytest

from lykke.application.commands.day import (
    UpdateReminderStatusCommand,
    UpdateReminderStatusHandler,
)
from lykke.core.exceptions import DomainError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity
from lykke.domain.events.day_events import ReminderStatusChangedEvent
from tests.unit.fakes import (
    _FakeDayReadOnlyRepo,
    _FakeReadOnlyRepos,
    _FakeUoW,
    _FakeUoWFactory,
)


@pytest.mark.asyncio
async def test_update_reminder_status_updates_status():
    """Test update_reminder_status updates the reminder's status."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_definition_ids=[],
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
    assert result.id == reminder.id
    assert result.status == value_objects.ReminderStatus.COMPLETE
    assert len(uow_factory.uow.added) == 1
    assert uow_factory.uow.added[0] == day
    updated_reminder = next(r for r in day.reminders if r.id == reminder.id)
    assert updated_reminder.status == value_objects.ReminderStatus.COMPLETE


@pytest.mark.asyncio
async def test_update_reminder_status_emits_domain_event():
    """Test update_reminder_status emits ReminderStatusChangedEvent."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_definition_ids=[],
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
    events = day.collect_events()
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
        routine_definition_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    fake_reminder_id = uuid4()

    day_repo = _FakeDayReadOnlyRepo(day)
    ro_repos = _FakeReadOnlyRepos(day_repo=day_repo)
    uow = _FakeUoW(day_repo=day_repo)
    uow_factory = _FakeUoWFactory(uow)
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
        routine_definition_ids=[],
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
    ro_repos = _FakeReadOnlyRepos(day_repo=day_repo)
    uow = _FakeUoW(day_repo=day_repo)
    uow_factory = _FakeUoWFactory(uow)
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
    assert result.status == value_objects.ReminderStatus.COMPLETE
    # No events should be emitted
    events = day.collect_events()
    assert len(events) == 0


@pytest.mark.asyncio
async def test_update_reminder_status_all_status_transitions():
    """Test update_reminder_status works for all status transitions."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_definition_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    reminder = day.add_reminder("Test Reminder")

    day_repo = _FakeDayReadOnlyRepo(day)
    ro_repos = _FakeReadOnlyRepos(day_repo=day_repo)
    uow = _FakeUoW(day_repo=day_repo)
    uow_factory = _FakeUoWFactory(uow)
    handler = UpdateReminderStatusHandler(ro_repos, uow_factory, user_id)

    # INCOMPLETE -> COMPLETE
    result = await handler.handle(
        UpdateReminderStatusCommand(
            date=task_date,
            reminder_id=reminder.id,
            status=value_objects.ReminderStatus.COMPLETE,
        )
    )
    assert result.status == value_objects.ReminderStatus.COMPLETE
    day_repo._day = uow_factory.uow.added[-1]

    # COMPLETE -> PUNT
    result = await handler.handle(
        UpdateReminderStatusCommand(
            date=task_date,
            reminder_id=reminder.id,
            status=value_objects.ReminderStatus.PUNT,
        )
    )
    assert result.status == value_objects.ReminderStatus.PUNT

    # Update the day in repo for next test
    day_repo._day = uow_factory.uow.added[-1]

    # PUNT -> INCOMPLETE
    result = await handler.handle(
        UpdateReminderStatusCommand(
            date=task_date,
            reminder_id=reminder.id,
            status=value_objects.ReminderStatus.INCOMPLETE,
        )
    )
    assert result.status == value_objects.ReminderStatus.INCOMPLETE
