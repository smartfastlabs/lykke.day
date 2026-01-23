"""Unit tests for CreateAdhocTaskHandler."""

from datetime import date as dt_date, time as dt_time
from uuid import uuid4

import pytest

from lykke.application.commands.task import CreateAdhocTaskCommand, CreateAdhocTaskHandler
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity
from tests.unit.application.commands.test_schedule_day import (
    _FakeCalendarEntryReadOnlyRepo,
    _FakeDayReadOnlyRepo,
    _FakeDayTemplateReadOnlyRepo,
    _FakeReadOnlyRepos,
    _FakeTaskReadOnlyRepo,
    _FakeUoWFactory,
)


@pytest.mark.asyncio
async def test_create_adhoc_task_sets_adhoc_fields():
    """Verify adhoc task uses ADHOC type and ONCE frequency."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)
    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )
    day = DayEntity.create_for_date(task_date, user_id, template)

    day_repo = _FakeDayReadOnlyRepo(day)
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    task_repo = _FakeTaskReadOnlyRepo([])
    calendar_entry_repo = _FakeCalendarEntryReadOnlyRepo([])
    ro_repos = _FakeReadOnlyRepos(
        day_template_repo, day_repo, task_repo, calendar_entry_repo
    )
    uow_factory = _FakeUoWFactory(
        day_template_repo, day_repo, task_repo, calendar_entry_repo
    )
    handler = CreateAdhocTaskHandler(ro_repos, uow_factory, user_id)

    schedule = value_objects.TaskSchedule(
        available_time=dt_time(9, 0),
        timing_type=value_objects.TimingType.FIXED_TIME,
    )

    result = await handler.handle(
        CreateAdhocTaskCommand(
            scheduled_date=task_date,
            name="Adhoc task",
            category=value_objects.TaskCategory.WORK,
            description="One-off task",
            schedule=schedule,
            tags=[value_objects.TaskTag.IMPORTANT],
        )
    )

    assert result.type == value_objects.TaskType.ADHOC
    assert result.frequency == value_objects.TaskFrequency.ONCE
    assert result.routine_id is None
    assert result.status == value_objects.TaskStatus.NOT_STARTED
    assert result.schedule == schedule
    assert result.tags == [value_objects.TaskTag.IMPORTANT]
