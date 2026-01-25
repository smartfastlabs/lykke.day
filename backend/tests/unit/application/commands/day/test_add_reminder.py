"""Unit tests for AddReminderToDayHandler."""

from datetime import date as dt_date
from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.commands.day import (
    AddReminderToDayCommand,
    AddReminderToDayHandler,
)
from lykke.core.exceptions import DomainError, NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity, UserEntity
from lykke.domain.events.day_events import ReminderAddedEvent
from tests.support.dobles import (
    create_day_repo_double,
    create_day_template_repo_double,
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
    create_user_repo_double,
)


@pytest.mark.asyncio
async def test_add_reminder_adds_reminder_to_existing_day():
    """Test add_reminder adds a reminder to an existing day."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_definition_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)

    day_repo = create_day_repo_double()
    day_id = DayEntity.id_from_date_and_user(task_date, user_id)
    allow(day_repo).get.with_args(day_id).and_return(day)

    day_template_repo = create_day_template_repo_double()
    allow(day_template_repo).get.and_return(template)
    allow(day_template_repo).search_one.and_return(template)

    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = create_user_repo_double()
    allow(user_repo).get.with_args(user_id).and_return(user)

    ro_repos = create_read_only_repos_double(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow = create_uow_double(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow_factory = create_uow_factory_double(uow)
    handler = AddReminderToDayHandler(ro_repos, uow_factory, user_id)

    # Act
    result = await handler.handle(
        AddReminderToDayCommand(date=task_date, reminder="Test Reminder")
    )

    # Assert
    assert result.name == "Test Reminder"
    assert result.status == value_objects.ReminderStatus.INCOMPLETE
    assert len(uow.added) == 1
    assert uow.added[0] == day
    assert len(day.reminders) == 1
    assert day.reminders[0].id == result.id


@pytest.mark.asyncio
async def test_add_reminder_emits_domain_event():
    """Test add_reminder emits ReminderAddedEvent."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_definition_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)

    day_repo = create_day_repo_double()
    day_id = DayEntity.id_from_date_and_user(task_date, user_id)
    allow(day_repo).get.with_args(day_id).and_return(day)

    day_template_repo = create_day_template_repo_double()
    allow(day_template_repo).get.and_return(template)
    allow(day_template_repo).search_one.and_return(template)

    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = create_user_repo_double()
    allow(user_repo).get.with_args(user_id).and_return(user)

    ro_repos = create_read_only_repos_double(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow = create_uow_double(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow_factory = create_uow_factory_double(uow)
    handler = AddReminderToDayHandler(ro_repos, uow_factory, user_id)

    # Act
    result = await handler.handle(
        AddReminderToDayCommand(date=task_date, reminder="Test Reminder")
    )

    # Assert
    events = day.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], ReminderAddedEvent)
    assert events[0].reminder_name == "Test Reminder"
    assert events[0].day_id == day.id


@pytest.mark.asyncio
async def test_add_reminder_raises_if_day_missing():
    """Test add_reminder raises if the day doesn't exist."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_definition_ids=[],
        time_blocks=[],
    )

    day_repo = create_day_repo_double()
    day_id = DayEntity.id_from_date_and_user(task_date, user_id)
    allow(day_repo).get.with_args(day_id).and_raise(NotFoundError("Day not found"))

    day_template_repo = create_day_template_repo_double()
    allow(day_template_repo).get.and_return(template)
    allow(day_template_repo).search_one.and_return(template)

    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = create_user_repo_double()
    allow(user_repo).get.with_args(user_id).and_return(user)

    ro_repos = create_read_only_repos_double(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow = create_uow_double(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow_factory = create_uow_factory_double(uow)
    handler = AddReminderToDayHandler(ro_repos, uow_factory, user_id)

    # Act / Assert
    with pytest.raises(NotFoundError, match="Day"):
        await handler.handle(
            AddReminderToDayCommand(date=task_date, reminder="Test Reminder")
        )


@pytest.mark.asyncio
async def test_add_reminder_enforces_max_five():
    """Test add_reminder enforces maximum of 5 reminders."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_definition_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    day.add_reminder("Reminder 1")
    day.add_reminder("Reminder 2")
    day.add_reminder("Reminder 3")
    day.add_reminder("Reminder 4")
    day.add_reminder("Reminder 5")

    day_repo = create_day_repo_double()
    day_id = DayEntity.id_from_date_and_user(task_date, user_id)
    allow(day_repo).get.with_args(day_id).and_return(day)

    day_template_repo = create_day_template_repo_double()
    allow(day_template_repo).get.and_return(template)
    allow(day_template_repo).search_one.and_return(template)

    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = create_user_repo_double()
    allow(user_repo).get.with_args(user_id).and_return(user)

    ro_repos = create_read_only_repos_double(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow = create_uow_double(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow_factory = create_uow_factory_double(uow)
    handler = AddReminderToDayHandler(ro_repos, uow_factory, user_id)

    # Act & Assert
    with pytest.raises(DomainError, match="at most 5 active reminders"):
        await handler.handle(
            AddReminderToDayCommand(date=task_date, reminder="Reminder 6")
        )
