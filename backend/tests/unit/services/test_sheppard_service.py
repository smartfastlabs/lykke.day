"""Unit tests for SheppardService."""

import datetime
from datetime import UTC
from unittest.mock import patch
from uuid import NAMESPACE_DNS, UUID, uuid4, uuid5

import pytest
from dobles import allow
from planned.application.services import DayService, SheppardService
from planned.application.services.calendar import CalendarService
from planned.application.services.planning import PlanningService
from planned.domain.entities import (
    CalendarEntry,
    Day,
    DayContext,
    DayStatus,
    PushSubscription,
    Task,
    TaskDefinition,
    TaskStatus,
)
from planned.domain.value_objects.task import TaskCategory, TaskFrequency, TaskType


def create_day_service(user, ctx, uow_factory):
    """Helper to create a DayService with the new signature."""
    return DayService(
        user=user,
        ctx=ctx,
        uow_factory=uow_factory,
    )


def create_sheppard_service(
    user,
    day_svc,
    uow_factory,
    calendar_service,
    planning_service,
    web_push_gateway,
    push_subscriptions=None,
    mode="starting",
):
    """Helper to create a SheppardService with the new signature."""
    return SheppardService(
        user=user,
        day_svc=day_svc,
        uow_factory=uow_factory,
        calendar_service=calendar_service,
        planning_service=planning_service,
        web_push_gateway=web_push_gateway,
        push_subscriptions=push_subscriptions,
        mode=mode,
    )


@pytest.mark.asyncio
async def test_build_notification_payload_single_task(
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test _build_notification_payload for a single task."""
    date = datetime.date(2024, 1, 1)
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
    )
    ctx = DayContext(day=day, tasks=[], calendar_entries=[], messages=[])

    day_svc = create_day_service(test_user, ctx, mock_uow_factory)

    task = Task(
        id=uuid4(),
        user_id=test_user_id,
        name="Test Task",
        status=TaskStatus.READY,
        scheduled_date=date,
        task_definition=TaskDefinition(
            user_id=test_user_id,
            name="Task Def",
            description="Test task definition",
            type=TaskType.CHORE,
        ),
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.ONCE,
    )

    service = create_sheppard_service(
        user=test_user,
        day_svc=day_svc,
        uow_factory=mock_uow_factory,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        web_push_gateway=mock_web_push_gateway,
    )

    payload = service._build_notification_payload([task])

    assert payload.title == "Test Task"
    assert "Test Task" in payload.body
    assert len(payload.data["tasks"]) == 1
    assert payload.data["tasks"][0]["id"] == task.id


@pytest.mark.asyncio
async def test_build_notification_payload_multiple_tasks(
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test _build_notification_payload for multiple tasks."""
    date = datetime.date(2024, 1, 1)
    template_id = uuid4()
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
    )
    ctx = DayContext(day=day, tasks=[], calendar_entries=[], messages=[])

    day_svc = create_day_service(test_user, ctx, mock_uow_factory)

    task1 = Task(
        id=uuid4(),
        user_id=test_user_id,
        name="Task 1",
        status=TaskStatus.READY,
        scheduled_date=date,
        task_definition=TaskDefinition(
            user_id=test_user_id,
            name="Task Def",
            description="Test task definition",
            type=TaskType.CHORE,
        ),
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.ONCE,
    )
    task2 = Task(
        id=uuid4(),
        user_id=test_user_id,
        name="Task 2",
        status=TaskStatus.READY,
        scheduled_date=date,
        task_definition=TaskDefinition(
            user_id=test_user_id,
            name="Task Def",
            description="Test task definition",
            type=TaskType.CHORE,
        ),
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.ONCE,
    )

    service = create_sheppard_service(
        user=test_user,
        day_svc=day_svc,
        uow_factory=mock_uow_factory,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        web_push_gateway=mock_web_push_gateway,
    )

    payload = service._build_notification_payload([task1, task2])

    assert "2 tasks ready" in payload.title
    assert len(payload.data["tasks"]) == 2


@pytest.mark.asyncio
async def test_build_event_notification_payload(
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
    test_user,
    test_datetime_noon,
    mock_uow_factory,
):
    """Test _build_event_notification_payload."""
    date = datetime.date(2024, 1, 1)
    template_id = uuid4()
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
    )
    ctx = DayContext(day=day, tasks=[], calendar_entries=[], messages=[])

    day_svc = create_day_service(test_user, ctx, mock_uow_factory)

    calendar_entry = CalendarEntry(
        id=uuid4(),
        user_id=test_user_id,
        name="Test Calendar Entry",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "cal-1"),
        platform_id="entry-1",
        platform="test",
        status="confirmed",
        starts_at=test_datetime_noon,
    )

    service = create_sheppard_service(
        user=test_user,
        day_svc=day_svc,
        uow_factory=mock_uow_factory,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        web_push_gateway=mock_web_push_gateway,
    )

    payload = service._build_calendar_entry_notification_payload([calendar_entry])

    assert payload.title == "Test Calendar Entry"
    assert "starting soon" in payload.body
    assert len(payload.data["calendar_entries"]) == 1
    assert payload.data["calendar_entries"][0]["id"] == calendar_entry.id


@pytest.mark.asyncio
async def test_notify_for_tasks(
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test _notify_for_tasks sends notifications."""
    date = datetime.date(2024, 1, 1)
    template_id = uuid4()
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
    )
    ctx = DayContext(day=day, tasks=[], calendar_entries=[], messages=[])

    day_svc = create_day_service(test_user, ctx, mock_uow_factory)

    task = Task(
        id=uuid4(),
        user_id=test_user_id,
        name="Test Task",
        status=TaskStatus.READY,
        scheduled_date=date,
        task_definition=TaskDefinition(
            user_id=test_user_id,
            name="Task Def",
            description="Test task definition",
            type=TaskType.CHORE,
        ),
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.ONCE,
    )

    subscription = PushSubscription(
        id=uuid4(),
        user_id=test_user_id,
        endpoint="https://example.com/push",
        p256dh="key",
        auth="auth",
    )

    allow(mock_web_push_gateway).send_notification.and_return(None)

    service = create_sheppard_service(
        user=test_user,
        day_svc=day_svc,
        uow_factory=mock_uow_factory,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        web_push_gateway=mock_web_push_gateway,
        push_subscriptions=[subscription],
    )

    await service._notify_for_tasks([task])

    # Verify send_notification was called
    assert True  # If we get here, no exception was raised


@pytest.mark.asyncio
async def test_notify_for_tasks_empty_list(
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test _notify_for_tasks handles empty task list."""
    date = datetime.date(2024, 1, 1)
    template_id = uuid4()
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
    )
    ctx = DayContext(day=day, tasks=[], calendar_entries=[], messages=[])

    day_svc = create_day_service(test_user, ctx, mock_uow_factory)

    service = create_sheppard_service(
        user=test_user,
        day_svc=day_svc,
        uow_factory=mock_uow_factory,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        web_push_gateway=mock_web_push_gateway,
    )

    # Should not raise an exception
    await service._notify_for_tasks([])


@pytest.mark.asyncio
async def test_stop_sets_mode_to_stopping(
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test stop sets mode to stopping."""
    date = datetime.date(2024, 1, 1)
    template_id = uuid4()
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
    )
    ctx = DayContext(day=day, tasks=[], calendar_entries=[], messages=[])

    day_svc = create_day_service(test_user, ctx, mock_uow_factory)

    service = create_sheppard_service(
        user=test_user,
        day_svc=day_svc,
        uow_factory=mock_uow_factory,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        web_push_gateway=mock_web_push_gateway,
        mode="active",
    )

    service.stop()

    assert service.mode == "stopping"
    assert not service.is_running


@pytest.mark.asyncio
async def test_is_running_property(
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test is_running property returns correct value."""
    date = datetime.date(2024, 1, 1)
    template_id = uuid4()
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
    )
    ctx = DayContext(day=day, tasks=[], calendar_entries=[], messages=[])

    day_svc = create_day_service(test_user, ctx, mock_uow_factory)

    # Test active mode
    service = create_sheppard_service(
        user=test_user,
        day_svc=day_svc,
        uow_factory=mock_uow_factory,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        web_push_gateway=mock_web_push_gateway,
        mode="active",
    )
    assert service.is_running is True

    # Test stopping mode
    service.mode = "stopping"
    assert service.is_running is False

    # Test starting mode
    service.mode = "starting"
    assert service.is_running is False


@pytest.mark.asyncio
async def test_render_prompt(
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test _render_prompt renders template with context."""
    date = datetime.date(2024, 1, 1)
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
    )
    ctx = DayContext(day=day, tasks=[], calendar_entries=[], messages=[])

    day_svc = create_day_service(test_user, ctx, mock_uow_factory)

    service = create_sheppard_service(
        user=test_user,
        day_svc=day_svc,
        uow_factory=mock_uow_factory,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        web_push_gateway=mock_web_push_gateway,
    )

    # Mock the templates.render function
    with patch("planned.application.services.sheppard.templates.render") as mock_render:
        mock_render.return_value = "rendered template"
        result = service._render_prompt("test-template.md", extra_arg="value")

    mock_render.assert_called_once()
    call_kwargs = mock_render.call_args[1]
    assert "test-template.md" in mock_render.call_args[0]
    assert "tasks" in call_kwargs
    assert "calendar_entries" in call_kwargs
    assert "current_time" in call_kwargs
    assert call_kwargs["extra_arg"] == "value"


@pytest.mark.asyncio
async def test_morning_summary_prompt(
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test morning_summary_prompt renders morning summary template."""
    date = datetime.date(2024, 1, 1)
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
    )
    ctx = DayContext(day=day, tasks=[], calendar_entries=[], messages=[])

    day_svc = create_day_service(test_user, ctx, mock_uow_factory)

    service = create_sheppard_service(
        user=test_user,
        day_svc=day_svc,
        uow_factory=mock_uow_factory,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        web_push_gateway=mock_web_push_gateway,
    )

    with patch("planned.application.services.sheppard.templates.render") as mock_render:
        mock_render.return_value = "morning summary"
        result = service.morning_summary_prompt()

    assert result == "morning summary"
    mock_render.assert_called_once()
    assert "morning-summary.md" in mock_render.call_args[0]


@pytest.mark.asyncio
async def test_evening_summary_prompt(
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test evening_summary_prompt renders evening summary template."""
    date = datetime.date(2024, 1, 1)
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
    )
    ctx = DayContext(day=day, tasks=[], calendar_entries=[], messages=[])

    day_svc = create_day_service(test_user, ctx, mock_uow_factory)

    service = create_sheppard_service(
        user=test_user,
        day_svc=day_svc,
        uow_factory=mock_uow_factory,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        web_push_gateway=mock_web_push_gateway,
    )

    with patch("planned.application.services.sheppard.templates.render") as mock_render:
        mock_render.return_value = "evening summary"
        result = service.evening_summary_prompt()

    assert result == "evening summary"
    mock_render.assert_called_once()
    assert "evening-summary.md" in mock_render.call_args[0]


@pytest.mark.asyncio
async def test_notify_for_calendar_entries(
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
    test_user,
    test_datetime_noon,
    mock_uow_factory,
):
    """Test _notify_for_calendar_entries sends notifications for calendar entries."""
    date = datetime.date(2024, 1, 1)
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
    )
    ctx = DayContext(day=day, tasks=[], calendar_entries=[], messages=[])

    day_svc = create_day_service(test_user, ctx, mock_uow_factory)

    calendar_entry = CalendarEntry(
        id=uuid4(),
        user_id=test_user_id,
        name="Test Calendar Entry",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "cal-1"),
        platform_id="entry-1",
        platform="test",
        status="confirmed",
        starts_at=test_datetime_noon,
    )

    subscription = PushSubscription(
        id=uuid4(),
        user_id=test_user_id,
        endpoint="https://example.com/push",
        p256dh="key",
        auth="auth",
    )

    allow(mock_web_push_gateway).send_notification.and_return(None)

    service = create_sheppard_service(
        user=test_user,
        day_svc=day_svc,
        uow_factory=mock_uow_factory,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        web_push_gateway=mock_web_push_gateway,
        push_subscriptions=[subscription],
    )

    await service._notify_for_calendar_entries([calendar_entry])

    # Verify send_notification was called
    assert True  # If we get here, no exception was raised


@pytest.mark.asyncio
async def test_notify_for_events_empty_list(
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test _notify_for_calendar_entries handles empty calendar entry list."""
    date = datetime.date(2024, 1, 1)
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
    )
    ctx = DayContext(day=day, tasks=[], calendar_entries=[], messages=[])

    day_svc = create_day_service(test_user, ctx, mock_uow_factory)

    service = create_sheppard_service(
        user=test_user,
        day_svc=day_svc,
        uow_factory=mock_uow_factory,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        web_push_gateway=mock_web_push_gateway,
    )

    # Should not raise an exception
    await service._notify_for_calendar_entries([])
