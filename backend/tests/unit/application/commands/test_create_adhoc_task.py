"""Unit tests for CreateAdhocTaskHandler."""

from datetime import date as dt_date, time as dt_time
from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.commands.task import (
    CreateAdhocTaskCommand,
    CreateAdhocTaskHandler,
)
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity, UserEntity
from tests.support.dobles import (
    create_calendar_entry_repo_double,
    create_day_repo_double,
    create_day_template_repo_double,
    create_read_only_repos_double,
    create_task_repo_double,
    create_uow_double,
    create_uow_factory_double,
)


@pytest.mark.asyncio
async def test_create_adhoc_task_sets_adhoc_fields():
    """Verify adhoc task uses ADHOC type and ONCE frequency."""
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

    task_repo = create_task_repo_double()
    allow(task_repo).search.and_return([])

    calendar_entry_repo = create_calendar_entry_repo_double()
    allow(calendar_entry_repo).search.and_return([])

    ro_repos = create_read_only_repos_double(
        day_template_repo=day_template_repo,
        day_repo=day_repo,
        task_repo=task_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    uow = create_uow_double(
        day_template_repo=day_template_repo,
        day_repo=day_repo,
        task_repo=task_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    uow_factory = create_uow_factory_double(uow)
    user = UserEntity(id=user_id, email="test@example.com", hashed_password="!")
    handler = CreateAdhocTaskHandler(ro_repos, uow_factory, user)

    time_window = value_objects.TimeWindow(
        available_time=dt_time(9, 0),
    )

    result = await handler.handle(
        CreateAdhocTaskCommand(
            scheduled_date=task_date,
            name="Adhoc task",
            category=value_objects.TaskCategory.WORK,
            description="One-off task",
            time_window=time_window,
            tags=[value_objects.TaskTag.IMPORTANT],
        )
    )

    assert result.type == value_objects.TaskType.ADHOC
    assert result.frequency == value_objects.TaskFrequency.ONCE
    assert result.routine_definition_id is None
    assert result.status == value_objects.TaskStatus.NOT_STARTED
    assert result.time_window == time_window
    assert result.tags == [value_objects.TaskTag.IMPORTANT]


@pytest.mark.asyncio
async def test_create_adhoc_task_with_reminder_type():
    """Verify creating a reminder task uses REMINDER type."""
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

    task_repo = create_task_repo_double()
    allow(task_repo).search.and_return([])

    calendar_entry_repo = create_calendar_entry_repo_double()
    allow(calendar_entry_repo).search.and_return([])

    ro_repos = create_read_only_repos_double(
        day_template_repo=day_template_repo,
        day_repo=day_repo,
        task_repo=task_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    uow = create_uow_double(
        day_template_repo=day_template_repo,
        day_repo=day_repo,
        task_repo=task_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    uow_factory = create_uow_factory_double(uow)
    user = UserEntity(id=user_id, email="test@example.com", hashed_password="!")
    handler = CreateAdhocTaskHandler(ro_repos, uow_factory, user)

    result = await handler.handle(
        CreateAdhocTaskCommand(
            scheduled_date=task_date,
            name="Test Reminder",
            category=value_objects.TaskCategory.PLANNING,
            type=value_objects.TaskType.REMINDER,
        )
    )

    assert result.type == value_objects.TaskType.REMINDER
    assert result.name == "Test Reminder"
    assert result.status == value_objects.TaskStatus.NOT_STARTED
    assert result.category == value_objects.TaskCategory.PLANNING
    assert result.frequency == value_objects.TaskFrequency.ONCE
