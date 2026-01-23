"""Unit tests for ScheduleDayHandler."""

from datetime import date as dt_date, time
from uuid import UUID, uuid4

import pytest

from lykke.application.commands.day import ScheduleDayCommand, ScheduleDayHandler
from lykke.domain import value_objects
from lykke.domain.entities import (
    DayEntity,
    DayTemplateEntity,
    TaskEntity,
    TimeBlockDefinitionEntity,
)
from lykke.domain.value_objects.time_block import TimeBlockCategory, TimeBlockType
from tests.unit.fakes import (
    _FakeCalendarEntryReadOnlyRepo,
    _FakeDayReadOnlyRepo,
    _FakeDayTemplateReadOnlyRepo,
    _FakePreviewDayHandler,
    _FakeReadOnlyRepos,
    _FakeTaskReadOnlyRepo,
    _FakeTimeBlockDefinitionReadOnlyRepo,
    _FakeUoW,
    _FakeUoWFactory,
)


@pytest.mark.asyncio
async def test_schedule_day_creates_day_and_tasks():
    """Verify schedule_day creates day and tasks."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    # Create test data
    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)

    tasks = [
        TaskEntity(
            id=uuid4(),
            user_id=user_id,
            scheduled_date=task_date,
            name="Task 1",
            status=value_objects.TaskStatus.READY,
            type=value_objects.TaskType.WORK,
            category=value_objects.TaskCategory.WORK,
            frequency=value_objects.TaskFrequency.ONCE,
        ),
        TaskEntity(
            id=uuid4(),
            user_id=user_id,
            scheduled_date=task_date,
            name="Task 2",
            status=value_objects.TaskStatus.READY,
            type=value_objects.TaskType.SOCIAL,
            category=value_objects.TaskCategory.WORK,
            frequency=value_objects.TaskFrequency.ONCE,
        ),
    ]

    # Setup repositories
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    day_repo = _FakeDayReadOnlyRepo(None)
    task_repo = _FakeTaskReadOnlyRepo([])
    calendar_entry_repo = _FakeCalendarEntryReadOnlyRepo([])
    ro_repos = _FakeReadOnlyRepos(
        day_template_repo=day_template_repo,
        day_repo=day_repo,
        task_repo=task_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    uow = _FakeUoW(
        day_template_repo=day_template_repo,
        day_repo=day_repo,
        task_repo=task_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    uow_factory = _FakeUoWFactory(uow)
    preview_handler = _FakePreviewDayHandler(day, tasks)

    handler = ScheduleDayHandler(ro_repos, uow_factory, user_id, preview_handler)

    # Act
    result = await handler.handle(
        ScheduleDayCommand(date=task_date, template_id=template.id)
    )

    # Assert
    assert result.day.date == task_date
    assert result.day.user_id == user_id
    assert result.day.status == value_objects.DayStatus.SCHEDULED
    assert len(result.tasks) == 2

    # Verify day was created
    assert len(uow_factory.uow.created_entities) >= 1
    created_day = [
        e for e in uow_factory.uow.created_entities if isinstance(e, DayEntity)
    ][0]
    assert created_day.date == task_date

    # Verify tasks were created
    created_tasks = [
        e for e in uow_factory.uow.created_entities if isinstance(e, TaskEntity)
    ]
    assert len(created_tasks) == 2


@pytest.mark.asyncio
async def test_schedule_day_returns_existing_day_without_creating():
    """Verify schedule_day returns existing day without creating tasks."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    tasks = [
        TaskEntity(
            id=uuid4(),
            user_id=user_id,
            scheduled_date=task_date,
            name="Task 1",
            status=value_objects.TaskStatus.READY,
            type=value_objects.TaskType.WORK,
            category=value_objects.TaskCategory.WORK,
            frequency=value_objects.TaskFrequency.ONCE,
        )
    ]

    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    day_repo = _FakeDayReadOnlyRepo(day)
    task_repo = _FakeTaskReadOnlyRepo(tasks)
    calendar_entry_repo = _FakeCalendarEntryReadOnlyRepo([])
    ro_repos = _FakeReadOnlyRepos(
        day_template_repo=day_template_repo,
        day_repo=day_repo,
        task_repo=task_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    uow = _FakeUoW(
        day_template_repo=day_template_repo,
        day_repo=day_repo,
        task_repo=task_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    uow_factory = _FakeUoWFactory(uow)
    preview_handler = _FakePreviewDayHandler(day, [])

    handler = ScheduleDayHandler(ro_repos, uow_factory, user_id, preview_handler)

    result = await handler.handle(
        ScheduleDayCommand(date=task_date, template_id=template.id)
    )

    assert result.day == day
    assert result.tasks == tasks
    assert len(uow_factory.uow.created_entities) == 0
    assert len(uow_factory.uow.bulk_deleted_tasks) == 0


@pytest.mark.asyncio
async def test_schedule_day_deletes_existing_tasks():
    """Verify schedule_day deletes existing tasks for the date."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)

    # Setup repositories
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    day_repo = _FakeDayReadOnlyRepo(None)
    task_repo = _FakeTaskReadOnlyRepo([])
    calendar_entry_repo = _FakeCalendarEntryReadOnlyRepo([])
    ro_repos = _FakeReadOnlyRepos(
        day_template_repo=day_template_repo,
        day_repo=day_repo,
        task_repo=task_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    uow = _FakeUoW(
        day_template_repo=day_template_repo,
        day_repo=day_repo,
        task_repo=task_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    uow_factory = _FakeUoWFactory(uow)
    preview_handler = _FakePreviewDayHandler(day, [])

    handler = ScheduleDayHandler(ro_repos, uow_factory, user_id, preview_handler)

    # Act
    await handler.handle(ScheduleDayCommand(date=task_date, template_id=template.id))

    # Assert - bulk delete should have been called
    assert len(uow_factory.uow.bulk_deleted_tasks) == 1
    delete_query = uow_factory.uow.bulk_deleted_tasks[0]
    assert delete_query.date == task_date
    assert delete_query.is_adhoc is False


@pytest.mark.asyncio
async def test_schedule_day_raises_error_if_no_template():
    """Verify schedule_day raises error if day has no template."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    # Create day without template
    day = DayEntity.create_for_date(task_date, user_id, template)
    day.template = None  # Remove template

    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    day_repo = _FakeDayReadOnlyRepo(None)
    task_repo = _FakeTaskReadOnlyRepo([])
    calendar_entry_repo = _FakeCalendarEntryReadOnlyRepo([])
    ro_repos = _FakeReadOnlyRepos(
        day_template_repo=day_template_repo,
        day_repo=day_repo,
        task_repo=task_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    uow = _FakeUoW(
        day_template_repo=day_template_repo,
        day_repo=day_repo,
        task_repo=task_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    uow_factory = _FakeUoWFactory(uow)
    preview_handler = _FakePreviewDayHandler(day, [])

    handler = ScheduleDayHandler(ro_repos, uow_factory, user_id, preview_handler)

    # Act & Assert
    with pytest.raises(ValueError, match="Day template is required to schedule"):
        await handler.handle(
            ScheduleDayCommand(date=task_date, template_id=template.id)
        )


@pytest.mark.asyncio
async def test_schedule_day_uses_template_id_if_provided():
    """Verify schedule_day uses provided template_id."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)

    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    day_repo = _FakeDayReadOnlyRepo(None)
    task_repo = _FakeTaskReadOnlyRepo([])
    calendar_entry_repo = _FakeCalendarEntryReadOnlyRepo([])
    ro_repos = _FakeReadOnlyRepos(
        day_template_repo=day_template_repo,
        day_repo=day_repo,
        task_repo=task_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    uow = _FakeUoW(
        day_template_repo=day_template_repo,
        day_repo=day_repo,
        task_repo=task_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    uow_factory = _FakeUoWFactory(uow)
    preview_handler = _FakePreviewDayHandler(day, [])

    handler = ScheduleDayHandler(ro_repos, uow_factory, user_id, preview_handler)

    # Act
    result = await handler.handle(
        ScheduleDayCommand(date=task_date, template_id=template.id)
    )

    # Assert
    assert result.day.template == template


@pytest.mark.asyncio
async def test_schedule_day_copies_timeblocks_from_template():
    """Verify schedule_day copies timeblocks from the day template to the day."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    # Create a time block definition
    time_block_def_id = uuid4()
    time_block_def = TimeBlockDefinitionEntity(
        id=time_block_def_id,
        user_id=user_id,
        name="Work Block",
        description="Focused work time",
        type=TimeBlockType.WORK,
        category=TimeBlockCategory.WORK,
    )

    # Create template with timeblocks
    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[
            value_objects.DayTemplateTimeBlock(
                time_block_definition_id=time_block_def_id,
                start_time=time(9, 0, 0),
                end_time=time(12, 0, 0),
                name="Morning Work",
            ),
            value_objects.DayTemplateTimeBlock(
                time_block_definition_id=time_block_def_id,
                start_time=time(14, 0, 0),
                end_time=time(17, 0, 0),
                name="Afternoon Work",
            ),
        ],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)

    # Setup repositories
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    day_repo = _FakeDayReadOnlyRepo(None)
    task_repo = _FakeTaskReadOnlyRepo([])
    calendar_entry_repo = _FakeCalendarEntryReadOnlyRepo([])
    time_block_def_repo = _FakeTimeBlockDefinitionReadOnlyRepo(
        {time_block_def_id: time_block_def}
    )
    ro_repos = _FakeReadOnlyRepos(
        day_template_repo=day_template_repo,
        day_repo=day_repo,
        task_repo=task_repo,
        calendar_entry_repo=calendar_entry_repo,
        time_block_definition_repo=time_block_def_repo,
    )
    uow = _FakeUoW(
        day_template_repo=day_template_repo,
        day_repo=day_repo,
        task_repo=task_repo,
        calendar_entry_repo=calendar_entry_repo,
        time_block_definition_repo=time_block_def_repo,
    )
    uow_factory = _FakeUoWFactory(uow)
    preview_handler = _FakePreviewDayHandler(day, [])

    handler = ScheduleDayHandler(ro_repos, uow_factory, user_id, preview_handler)

    # Act
    result = await handler.handle(
        ScheduleDayCommand(date=task_date, template_id=template.id)
    )

    # Assert - timeblocks should be copied from template to day
    assert len(result.day.time_blocks) == 2, (
        "Day should have 2 timeblocks copied from template"
    )

    # Verify first timeblock matches template
    day_tb1 = result.day.time_blocks[0]
    template_tb1 = template.time_blocks[0]
    assert day_tb1.time_block_definition_id == template_tb1.time_block_definition_id
    assert day_tb1.start_time == template_tb1.start_time
    assert day_tb1.end_time == template_tb1.end_time
    assert day_tb1.name == template_tb1.name

    # Verify second timeblock matches template
    day_tb2 = result.day.time_blocks[1]
    template_tb2 = template.time_blocks[1]
    assert day_tb2.time_block_definition_id == template_tb2.time_block_definition_id
    assert day_tb2.start_time == template_tb2.start_time
    assert day_tb2.end_time == template_tb2.end_time
    assert day_tb2.name == template_tb2.name

    # Verify the created day entity also has the timeblocks
    created_day = [
        e for e in uow_factory.uow.created_entities if isinstance(e, DayEntity)
    ][0]
    assert len(created_day.time_blocks) == 2, "Created day should have 2 timeblocks"


@pytest.mark.asyncio
async def test_schedule_day_copies_high_level_plan_from_template():
    """Verify schedule_day copies high_level_plan (including intentions) from template to day."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    # Create template with high_level_plan including intentions
    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
        high_level_plan=value_objects.HighLevelPlan(
            title="Focus Day",
            text="Get important work done",
            intentions=["Be present", "Stay off phone"],
        ),
    )

    day = DayEntity.create_for_date(task_date, user_id, template)

    # Setup repositories
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    day_repo = _FakeDayReadOnlyRepo(None)
    task_repo = _FakeTaskReadOnlyRepo([])
    calendar_entry_repo = _FakeCalendarEntryReadOnlyRepo([])
    ro_repos = _FakeReadOnlyRepos(
        day_template_repo=day_template_repo,
        day_repo=day_repo,
        task_repo=task_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    uow = _FakeUoW(
        day_template_repo=day_template_repo,
        day_repo=day_repo,
        task_repo=task_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    uow_factory = _FakeUoWFactory(uow)
    preview_handler = _FakePreviewDayHandler(day, [])

    handler = ScheduleDayHandler(ro_repos, uow_factory, user_id, preview_handler)

    # Act
    result = await handler.handle(
        ScheduleDayCommand(date=task_date, template_id=template.id)
    )

    # Assert - high_level_plan should be copied from template to day
    assert result.day.high_level_plan is not None
    assert result.day.high_level_plan.title == template.high_level_plan.title
    assert result.day.high_level_plan.text == template.high_level_plan.text
    assert result.day.high_level_plan.intentions == template.high_level_plan.intentions
    assert result.day.high_level_plan.intentions == ["Be present", "Stay off phone"]

    # Verify the created day entity also has the high_level_plan
    created_day = [
        e for e in uow_factory.uow.created_entities if isinstance(e, DayEntity)
    ][0]
    assert created_day.high_level_plan is not None
    assert created_day.high_level_plan.title == template.high_level_plan.title
    assert created_day.high_level_plan.text == template.high_level_plan.text
    assert created_day.high_level_plan.intentions == template.high_level_plan.intentions
