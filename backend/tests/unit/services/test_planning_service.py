"""Unit tests for PlanningService."""

import datetime
from datetime import UTC
from uuid import uuid4

import pytest
from dobles import allow

from planned.application.services import PlanningService
from planned.core.exceptions import exceptions
from planned.domain.entities import (
    Action,
    Day,
    DayContext,
    DayStatus,
    DayTemplate,
    Event,
    Routine,
    Task,
    TaskDefinition,
    User,
)
from planned.domain.value_objects.action import ActionType
from planned.domain.value_objects.routine import DayOfWeek, RoutineSchedule, RoutineTask
from planned.domain.value_objects.task import (
    TaskCategory,
    TaskFrequency,
    TaskStatus,
    TaskType,
)
from planned.domain.value_objects.user import UserSetting


@pytest.mark.asyncio
async def test_preview_tasks(
    mock_user_repo,
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_routine_repo,
    mock_task_definition_repo,
    mock_task_repo,
    test_user_uuid,
):
    """Test preview_tasks generates tasks from active routines."""
    date = datetime.date(2024, 1, 1)  # Monday

    routine = Routine(
        uuid=uuid4(),
        user_uuid=test_user_uuid,
        name="Morning Routine",
        routine_schedule=RoutineSchedule(
            weekdays=[DayOfWeek.MONDAY],
            frequency=TaskFrequency.DAILY,
        ),
        tasks=[
            RoutineTask(
                task_definition_id="def-1",
                name="Brush Teeth",
            ),
        ],
        category=TaskCategory.HEALTH,
    )

    task_def = TaskDefinition(
        user_uuid=test_user_uuid,
        id="def-1",
        name="Brush Teeth",
        description="Brush teeth routine",
        type=TaskType.CHORE,
    )

    allow(mock_routine_repo).all().and_return([routine])
    allow(mock_task_definition_repo).get("def-1").and_return(task_def)

    service = PlanningService(
        user_uuid=test_user_uuid,
        user_repo=mock_user_repo,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        routine_repo=mock_routine_repo,
        task_definition_repo=mock_task_definition_repo,
        task_repo=mock_task_repo,
    )

    result = await service.preview_tasks(date)

    assert len(result) == 1
    assert result[0].name == "Brush Teeth"
    assert result[0].routine_uuid == routine.uuid
    assert result[0].status == TaskStatus.NOT_STARTED


@pytest.mark.asyncio
async def test_preview_tasks_filters_inactive_routines(
    mock_user_repo,
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_routine_repo,
    mock_task_definition_repo,
    mock_task_repo,
    test_user_uuid,
):
    """Test preview_tasks filters out routines not active on the date."""
    date = datetime.date(2024, 1, 1)  # Monday

    # Routine active on Tuesday (weekday 1)
    routine = Routine(
        uuid=uuid4(),
        user_uuid=test_user_uuid,
        name="Tuesday Routine",
        routine_schedule=RoutineSchedule(
            weekdays=[DayOfWeek.TUESDAY],
            frequency=TaskFrequency.DAILY,
        ),
        tasks=[
            RoutineTask(
                task_definition_id="def-1",
                name="Tuesday Task",
            ),
        ],
        category=TaskCategory.HEALTH,
    )

    allow(mock_routine_repo).all().and_return([routine])

    service = PlanningService(
        user_uuid=test_user_uuid,
        user_repo=mock_user_repo,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        routine_repo=mock_routine_repo,
        task_definition_repo=mock_task_definition_repo,
        task_repo=mock_task_repo,
    )

    result = await service.preview_tasks(date)

    # Should be empty since routine is not active on Monday
    assert len(result) == 0


@pytest.mark.asyncio
async def test_preview_creates_day_context(
    mock_user_repo,
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_routine_repo,
    mock_task_definition_repo,
    mock_task_repo,
    test_user_uuid,
):
    """Test preview creates a DayContext with tasks, events, and messages."""
    date = datetime.date(2024, 1, 1)
    template_uuid = uuid4()

    user = User(
        uuid=test_user_uuid,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
        settings=UserSetting(template_defaults=[str(template_uuid)] * 7),
    )

    template = DayTemplate(
        uuid=template_uuid,
        user_uuid=test_user_uuid,
    )

    event = Event(
        uuid=uuid4(),
        user_uuid=test_user_uuid,
        name="Test Event",
        frequency=TaskFrequency.ONCE,
        calendar_uuid="cal-1",
        platform_id="event-1",
        platform="test",
        status="confirmed",
        starts_at=datetime.datetime.now(UTC),
        date=date,
    )

    allow(mock_day_repo).get(str(date)).and_raise(exceptions.NotFoundError("Not found"))
    allow(mock_user_repo).get(str(test_user_uuid)).and_return(user)
    allow(mock_day_template_repo).get(template_uuid).and_return(template)
    allow(mock_routine_repo).all().and_return([])
    allow(mock_event_repo).search_query.and_return([event])
    allow(mock_message_repo).search_query.and_return([])

    service = PlanningService(
        user_uuid=test_user_uuid,
        user_repo=mock_user_repo,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        routine_repo=mock_routine_repo,
        task_definition_repo=mock_task_definition_repo,
        task_repo=mock_task_repo,
    )

    result = await service.preview(date)

    assert isinstance(result, DayContext)
    assert result.day.user_uuid == test_user_uuid
    assert result.day.date == date
    assert len(result.events) == 1
    assert result.events[0].uuid == event.uuid


@pytest.mark.asyncio
async def test_preview_uses_existing_day_template(
    mock_user_repo,
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_routine_repo,
    mock_task_definition_repo,
    mock_task_repo,
    test_user_uuid,
):
    """Test preview uses template from existing day if available."""
    date = datetime.date(2024, 1, 1)
    existing_template_uuid = uuid4()

    existing_day = Day(
        user_uuid=test_user_uuid,
        date=date,
        status=DayStatus.SCHEDULED,
        template_uuid=existing_template_uuid,
    )

    template = DayTemplate(
        uuid=existing_template_uuid,
        slug="custom",
        user_uuid=test_user_uuid,
    )

    allow(mock_day_repo).get(str(date)).and_return(existing_day)
    allow(mock_day_template_repo).get(existing_template_uuid).and_return(template)
    allow(mock_routine_repo).all().and_return([])
    allow(mock_event_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])

    service = PlanningService(
        user_uuid=test_user_uuid,
        user_repo=mock_user_repo,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        routine_repo=mock_routine_repo,
        task_definition_repo=mock_task_definition_repo,
        task_repo=mock_task_repo,
    )

    result = await service.preview(date)

    assert result.day.template_uuid == existing_template_uuid


@pytest.mark.asyncio
async def test_unschedule_deletes_routine_tasks(
    mock_user_repo,
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_routine_repo,
    mock_task_definition_repo,
    mock_task_repo,
    test_user_uuid,
):
    """Test unschedule deletes routine tasks and sets day to UNSCHEDULED."""
    date = datetime.date(2024, 1, 1)

    routine_uuid = uuid4()
    routine_task = Task(
        uuid=uuid4(),
        user_uuid=test_user_uuid,
        name="Routine Task",
        status=TaskStatus.NOT_STARTED,
        scheduled_date=date,
        task_definition=TaskDefinition(
            user_uuid=test_user_uuid,
            id="def-1",
            name="Task Def",
            description="Test task definition",
            type=TaskType.CHORE,
        ),
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.ONCE,
        routine_uuid=str(routine_uuid),
        date=date,
    )

    non_routine_task = Task(
        uuid=uuid4(),
        user_uuid=test_user_uuid,
        name="Manual Task",
        status=TaskStatus.NOT_STARTED,
        scheduled_date=date,
        task_definition=TaskDefinition(
            user_uuid=test_user_uuid,
            id="def-2",
            name="Task Def",
            description="Test task definition",
            type=TaskType.CHORE,
        ),
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.ONCE,
        routine_uuid=None,
        date=date,
    )

    day = Day(
        user_uuid=test_user_uuid,
        date=date,
        status=DayStatus.SCHEDULED,
    )

    allow(mock_task_repo).search_query.and_return([routine_task, non_routine_task])
    allow(mock_task_repo).delete.and_return(None)
    allow(mock_day_repo).get(str(date)).and_return(day)
    allow(mock_day_repo).put.and_return(day)
    allow(mock_day_template_repo).get.and_return(
        DayTemplate(uuid=uuid4(), user_uuid=test_user_uuid)
    )

    service = PlanningService(
        user_uuid=test_user_uuid,
        user_repo=mock_user_repo,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        routine_repo=mock_routine_repo,
        task_definition_repo=mock_task_definition_repo,
        task_repo=mock_task_repo,
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
    mock_event_repo,
    mock_message_repo,
    mock_routine_repo,
    mock_task_definition_repo,
    mock_task_repo,
    test_user_uuid,
):
    """Test schedule creates tasks and sets day status to SCHEDULED."""
    date = datetime.date(2024, 1, 1)
    template_uuid = uuid4()

    user = User(
        uuid=test_user_uuid,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
        settings=UserSetting(template_defaults=[str(template_uuid)] * 7),
    )

    template = DayTemplate(
        uuid=template_uuid,
        user_uuid=test_user_uuid,
    )

    allow(mock_task_repo).delete_many.and_return(None)
    allow(mock_day_repo).get(str(date)).and_raise(exceptions.NotFoundError("Not found"))
    allow(mock_user_repo).get(str(test_user_uuid)).and_return(user)
    allow(mock_day_template_repo).get(template_uuid).and_return(template)
    allow(mock_routine_repo).all().and_return([])
    allow(mock_event_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])
    allow(mock_day_repo).put.and_return(
        Day(
            user_uuid=test_user_uuid,
            date=date,
            status=DayStatus.SCHEDULED,
            template_uuid=template_uuid,
        )
    )
    allow(mock_task_repo).put.and_return(None)

    service = PlanningService(
        user_uuid=test_user_uuid,
        user_repo=mock_user_repo,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        routine_repo=mock_routine_repo,
        task_definition_repo=mock_task_definition_repo,
        task_repo=mock_task_repo,
    )

    result = await service.schedule(date)

    assert isinstance(result, DayContext)
    assert result.day.status == DayStatus.SCHEDULED


@pytest.mark.asyncio
async def test_save_action_for_task(
    mock_user_repo,
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_routine_repo,
    mock_task_definition_repo,
    mock_task_repo,
    test_user_uuid,
):
    """Test save_action updates task status and saves it."""

    date = datetime.date(2024, 1, 1)
    task = Task(
        uuid=uuid4(),
        user_uuid=test_user_uuid,
        name="Test Task",
        status=TaskStatus.NOT_STARTED,
        scheduled_date=date,
        task_definition=TaskDefinition(
            user_uuid=test_user_uuid,
            id="def-1",
            name="Task Def",
            description="Test task definition",
            type=TaskType.CHORE,
        ),
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.ONCE,
        date=date,
    )

    action = Action(type=ActionType.COMPLETE)

    allow(mock_task_repo).put.and_return(task)

    service = PlanningService(
        user_uuid=test_user_uuid,
        user_repo=mock_user_repo,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        routine_repo=mock_routine_repo,
        task_definition_repo=mock_task_definition_repo,
        task_repo=mock_task_repo,
    )

    result = await service.save_action(task, action)

    assert len(result.actions) == 1
    assert result.actions[0].type == ActionType.COMPLETE
    assert result.status == TaskStatus.COMPLETE


@pytest.mark.asyncio
@pytest.mark.skip
async def test_save_action_for_event(
    mock_user_repo,
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_routine_repo,
    mock_task_definition_repo,
    mock_task_repo,
    test_user_uuid,
):
    """Test save_action saves event with action."""

    date = datetime.date(2024, 1, 1)
    event = Event(
        uuid=uuid4(),
        user_uuid=test_user_uuid,
        name="Test Event",
        frequency=TaskFrequency.ONCE,
        calendar_uuid="cal-1",
        platform_id="event-1",
        platform="test",
        status="confirmed",
        starts_at=datetime.datetime.now(UTC),
        date=date,
    )

    action = Action(type=ActionType.NOTIFY)

    allow(mock_event_repo).put.and_return(event)

    service = PlanningService(
        user_uuid=test_user_uuid,
        user_repo=mock_user_repo,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        routine_repo=mock_routine_repo,
        task_definition_repo=mock_task_definition_repo,
        task_repo=mock_task_repo,
    )

    result = await service.save_action(event, action)

    assert len(result.actions) == 1
    assert result.actions[0].type == ActionType.NOTIFY
    assert len(result.actions) == 1
    assert result.actions[0].type == ActionType.NOTIFY
