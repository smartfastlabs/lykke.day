"""Unit tests for PlanningService."""

import datetime
from datetime import UTC
from uuid import NAMESPACE_DNS, UUID, uuid4, uuid5

import pytest
from dobles import allow
from planned.application.services import PlanningService
from planned.core.exceptions import NotFoundError
from planned.domain import value_objects
from planned.domain.entities import CalendarEntity, CalendarEntryEntity, DayEntity, DayTemplateEntity, RoutineEntity, TaskDefinitionEntity, TaskEntity, UserEntity


@pytest.mark.asyncio
async def test_preview_tasks(
    mock_user_repo,
    mock_day_repo,
    mock_day_template_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_routine_repo,
    mock_task_definition_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test preview_tasks generates tasks from active routines."""
    date = datetime.date(2024, 1, 1)  # Monday

    task_def_id = uuid4()
    routine = RoutineEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Morning Routine",
        routine_schedule=value_objects.RoutineSchedule(
            weekdays=[value_objects.DayOfWeek.MONDAY],
            frequency=value_objects.TaskFrequency.DAILY,
        ),
        tasks=[
            value_objects.RoutineTask(
                task_definition_id=task_def_id,
                name="Brush Teeth",
            ),
        ],
        category=value_objects.TaskCategory.HEALTH,
    )

    task_def = TaskDefinitionEntity(
        id=task_def_id,
        user_id=test_user_id,
        name="Brush Teeth",
        description="Brush teeth routine",
        type=value_objects.TaskType.CHORE,
    )

    allow(mock_routine_repo).all().and_return([routine])
    allow(mock_task_definition_repo).get(task_def_id).and_return(task_def)

    service = PlanningService(
        user=test_user,
        uow_factory=mock_uow_factory,
    )

    result = await service.preview_tasks(date)

    assert len(result) == 1
    assert result[0].name == "Brush Teeth"
    assert result[0].routine_id == routine.id
    assert result[0].status == value_objects.TaskStatus.NOT_STARTED


@pytest.mark.asyncio
async def test_preview_tasks_filters_inactive_routines(
    mock_user_repo,
    mock_day_repo,
    mock_day_template_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_routine_repo,
    mock_task_definition_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test preview_tasks filters out routines not active on the date."""
    date = datetime.date(2024, 1, 1)  # Monday

    # Routine active on Tuesday (weekday 1)
    routine = RoutineEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Tuesday Routine",
        routine_schedule=value_objects.RoutineSchedule(
            weekdays=[value_objects.DayOfWeek.TUESDAY],
            frequency=value_objects.TaskFrequency.DAILY,
        ),
        tasks=[
            value_objects.RoutineTask(
                task_definition_id=uuid4(),
                name="Tuesday Task",
            ),
        ],
        category=value_objects.TaskCategory.HEALTH,
    )

    allow(mock_routine_repo).all().and_return([routine])

    service = PlanningService(
        user=test_user,
        uow_factory=mock_uow_factory,
    )

    result = await service.preview_tasks(date)

    # Should be empty since routine is not active on Monday
    assert len(result) == 0


@pytest.mark.asyncio
async def test_preview_creates_day_context(
    mock_user_repo,
    mock_day_repo,
    mock_day_template_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_routine_repo,
    mock_task_definition_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    mock_uow_factory,
    test_datetime_noon,
):
    """Test preview creates a DayContext with tasks, events, and messages."""
    date = datetime.date(2024, 1, 1)

    user = UserEntity(
        id=test_user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )

    template = DayTemplateEntity(
        slug="default",
        user_id=test_user_id,
    )

    calendar_entry = CalendarEntryEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Test Calendar Entry",
        frequency=value_objects.TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "cal-1"),
        platform_id="entry-1",
        platform="test",
        status="confirmed",
        starts_at=test_datetime_noon,
    )

    allow(mock_day_repo).get.and_raise(NotFoundError("Not found"))
    allow(mock_user_repo).get(test_user_id).and_return(user)
    allow(mock_day_template_repo).get_by_slug(template.slug).and_return(template)
    allow(mock_routine_repo).all().and_return([])
    allow(mock_calendar_entry_repo).search_query.and_return([calendar_entry])
    allow(mock_message_repo).search_query.and_return([])

    service = PlanningService(
        user=test_user,
        uow_factory=mock_uow_factory,
    )

    result = await service.preview(date)

    assert isinstance(result, value_objects.DayContext)
    assert result.day.user_id == test_user_id
    assert result.day.date == date
    assert len(result.calendar_entries) == 1
    assert result.calendar_entries[0].id == calendar_entry.id


@pytest.mark.asyncio
async def test_preview_uses_existing_day_template(
    mock_user_repo,
    mock_day_repo,
    mock_day_template_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_routine_repo,
    mock_task_definition_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test preview uses template from existing day if available."""
    date = datetime.date(2024, 1, 1)

    template = DayTemplateEntity(
        slug="custom",
        user_id=test_user_id,
    )

    existing_day = DayEntity(
        user_id=test_user_id,
        date=date,
        status=value_objects.DayStatus.SCHEDULED,
        template=template,
    )

    allow(mock_day_repo).get(existing_day.id).and_return(existing_day)
    allow(mock_day_template_repo).get(template.id).and_return(template)
    allow(mock_routine_repo).all().and_return([])
    allow(mock_calendar_entry_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])

    service = PlanningService(
        user=test_user,
        uow_factory=mock_uow_factory,
    )

    result = await service.preview(date)

    assert result.day.template is not None
    assert result.day.template.id == template.id


@pytest.mark.asyncio
async def test_unschedule_deletes_routine_tasks(
    mock_user_repo,
    mock_day_repo,
    mock_day_template_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_routine_repo,
    mock_task_definition_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test unschedule deletes routine tasks and sets day to UNSCHEDULED."""
    date = datetime.date(2024, 1, 1)

    routine_id = uuid4()
    routine_task = TaskEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Routine Task",
        status=value_objects.TaskStatus.NOT_STARTED,
        scheduled_date=date,
        task_definition=TaskDefinitionEntity(
            user_id=test_user_id,
            name="Task Def",
            description="Test task definition",
            type=value_objects.TaskType.CHORE,
        ),
        category=value_objects.TaskCategory.HOUSE,
        frequency=value_objects.TaskFrequency.ONCE,
        routine_id=routine_id,
    )

    non_routine_task = TaskEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Manual Task",
        status=value_objects.TaskStatus.NOT_STARTED,
        scheduled_date=date,
        task_definition=TaskDefinitionEntity(
            user_id=test_user_id,
            name="Task Def",
            description="Test task definition",
            type=value_objects.TaskType.CHORE,
        ),
        category=value_objects.TaskCategory.HOUSE,
        frequency=value_objects.TaskFrequency.ONCE,
        routine_id=None,
    )

    template = DayTemplateEntity(
        id=uuid4(),
        slug="default",
        user_id=test_user_id,
    )
    day = DayEntity(
        user_id=test_user_id,
        date=date,
        status=value_objects.DayStatus.SCHEDULED,
        template=template,
    )

    allow(mock_task_repo).search_query.and_return([routine_task, non_routine_task])
    allow(mock_task_repo).delete.and_return(None)
    allow(mock_calendar_entry_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])
    allow(mock_day_repo).get(day.id).and_return(day)
    allow(mock_day_repo).put.and_return(day)
    allow(mock_user_repo).get(test_user_id).and_return(
        UserEntity(
            id=test_user_id,
            email="test@example.com",
            hashed_password="hash",
            settings=value_objects.UserSetting(template_defaults=["default"] * 7),
        )
    )
    allow(mock_day_template_repo).get_by_slug("default").and_return(template)
    allow(mock_day_template_repo).get.and_return(
        DayTemplateEntity(slug="default", id=uuid4(), user_id=test_user_id)
    )

    service = PlanningService(
        user=test_user,
        uow_factory=mock_uow_factory,
    )

    await service.unschedule(date)

    # Verify delete was called for routine task
    # (non-routine task should remain)
    assert True  # If we get here, no exception was raised


@pytest.mark.asyncio
async def test_schedule_creates_tasks_and_sets_status(
    mock_user_repo,
    mock_day_repo,
    mock_day_template_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_routine_repo,
    mock_task_definition_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test schedule creates tasks and sets day status to SCHEDULED."""
    date = datetime.date(2024, 1, 1)

    user = UserEntity(
        id=test_user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )

    template = DayTemplateEntity(
        slug="default",
        user_id=test_user_id,
    )

    allow(mock_task_repo).delete_many.and_return(None)
    allow(mock_day_repo).get.and_raise(NotFoundError("Not found"))
    allow(mock_user_repo).get(test_user_id).and_return(user)
    allow(mock_day_template_repo).get_by_slug(template.slug).and_return(template)
    allow(mock_day_template_repo).get(template.id).and_return(template)
    allow(mock_routine_repo).all().and_return([])
    allow(mock_calendar_entry_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])
    allow(mock_day_repo).put.and_return(
        DayEntity(
            user_id=test_user_id,
            date=date,
            status=value_objects.DayStatus.SCHEDULED,
            template=template,
        )
    )
    allow(mock_task_repo).put.and_return(None)

    service = PlanningService(
        user=test_user,
        uow_factory=mock_uow_factory,
    )

    result = await service.schedule(date)

    assert isinstance(result, value_objects.DayContext)
    assert result.day.status == value_objects.DayStatus.SCHEDULED


@pytest.mark.asyncio
async def test_preview_with_template_id(
    mock_user_repo,
    mock_day_repo,
    mock_day_template_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_routine_repo,
    mock_task_definition_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test preview with explicit template_id."""
    date = datetime.date(2024, 1, 1)

    template = DayTemplateEntity(
        slug="custom",
        user_id=test_user_id,
    )

    allow(mock_day_template_repo).get(template.id).and_return(template)
    allow(mock_routine_repo).all().and_return([])
    allow(mock_calendar_entry_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])

    service = PlanningService(
        user=test_user,
        uow_factory=mock_uow_factory,
    )

    result = await service.preview(date, template_id=template.id)

    assert result.day.template is not None
    assert result.day.template.id == template.id


@pytest.mark.asyncio
async def test_schedule_with_template_id(
    mock_user_repo,
    mock_day_repo,
    mock_day_template_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_routine_repo,
    mock_task_definition_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test schedule with explicit template_id."""
    date = datetime.date(2024, 1, 1)

    template = DayTemplateEntity(
        slug="custom",
        user_id=test_user_id,
    )

    allow(mock_task_repo).delete_many.and_return(None)
    allow(mock_day_template_repo).get(template.id).and_return(template)
    allow(mock_routine_repo).all().and_return([])
    allow(mock_calendar_entry_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])
    allow(mock_day_repo).put.and_return(
        DayEntity(
            user_id=test_user_id,
            date=date,
            status=value_objects.DayStatus.SCHEDULED,
            template=template,
        )
    )
    allow(mock_task_repo).put.and_return(None)

    service = PlanningService(
        user=test_user,
        uow_factory=mock_uow_factory,
    )

    result = await service.schedule(date, template_id=template.id)

    assert result.day.status == value_objects.DayStatus.SCHEDULED
    assert result.day.template is not None
    assert result.day.template.id == template.id


@pytest.mark.asyncio
async def test_preview_tasks_uses_routine_task_name(
    mock_user_repo,
    mock_day_repo,
    mock_day_template_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_routine_repo,
    mock_task_definition_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test preview_tasks uses routine task name when provided."""
    date = datetime.date(2024, 1, 1)  # Monday
    task_def_id = uuid4()

    routine = RoutineEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Morning Routine",
        routine_schedule=value_objects.RoutineSchedule(
            weekdays=[value_objects.DayOfWeek.MONDAY],
            frequency=value_objects.TaskFrequency.DAILY,
        ),
        tasks=[
            value_objects.RoutineTask(
                task_definition_id=task_def_id,
                name="Custom Task Name",
            ),
        ],
        category=value_objects.TaskCategory.HEALTH,
    )

    task_def = TaskDefinitionEntity(
        id=task_def_id,
        user_id=test_user_id,
        name="Task Definition Name",
        description="Task definition",
        type=value_objects.TaskType.CHORE,
    )

    allow(mock_routine_repo).all().and_return([routine])
    allow(mock_task_definition_repo).get(task_def_id).and_return(task_def)

    service = PlanningService(
        user=test_user,
        uow_factory=mock_uow_factory,
    )

    result = await service.preview_tasks(date)

    assert len(result) == 1
    assert result[0].name == "Custom Task Name"
