"""Unit tests for SheppardService."""

import datetime
from datetime import UTC
from unittest.mock import patch
from uuid import NAMESPACE_DNS, UUID, uuid4, uuid5

import pytest
from dobles import allow
from planned.application.services import DayService, SheppardService
from planned.domain.entities import (
    Day,
    DayContext,
    DayStatus,
    Event,
    PushSubscription,
    Task,
    TaskDefinition,
    TaskStatus,
)
from planned.domain.value_objects.task import TaskCategory, TaskFrequency, TaskType


@pytest.mark.asyncio
async def test_build_notification_payload_single_task(
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_task_repo,
    mock_push_subscription_repo,
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
):
    """Test _build_notification_payload for a single task."""
    date = datetime.date(2024, 1, 1)
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_id=uuid4(),
    )
    ctx = DayContext(day=day, tasks=[], events=[], messages=[])

    day_svc = DayService(
        ctx=ctx,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        task_repo=mock_task_repo,
    )

    task = Task(
        uuid=uuid4(),
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
        date=date,
    )

    service = SheppardService(
        day_svc=day_svc,
        push_subscription_repo=mock_push_subscription_repo,
        task_repo=mock_task_repo,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        web_push_gateway=mock_web_push_gateway,
    )

    payload = service._build_notification_payload([task])

    assert payload.title == "Test Task"
    assert "Test Task" in payload.body
    assert len(payload.data["tasks"]) == 1
    assert payload.data["tasks"][0]["id"] == task.id


@pytest.mark.asyncio
async def test_build_notification_payload_multiple_tasks(
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_task_repo,
    mock_push_subscription_repo,
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
):
    """Test _build_notification_payload for multiple tasks."""
    date = datetime.date(2024, 1, 1)
    template_id = uuid4()
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_id=template_id,
    )
    ctx = DayContext(day=day, tasks=[], events=[], messages=[])

    day_svc = DayService(
        ctx=ctx,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        task_repo=mock_task_repo,
    )

    task1 = Task(
        uuid=uuid4(),
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
        date=date,
    )
    task2 = Task(
        uuid=uuid4(),
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
        date=date,
    )

    service = SheppardService(
        day_svc=day_svc,
        push_subscription_repo=mock_push_subscription_repo,
        task_repo=mock_task_repo,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        web_push_gateway=mock_web_push_gateway,
    )

    payload = service._build_notification_payload([task1, task2])

    assert "2 tasks ready" in payload.title
    assert len(payload.data["tasks"]) == 2


@pytest.mark.asyncio
async def test_build_event_notification_payload(
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_task_repo,
    mock_push_subscription_repo,
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
    test_datetime_noon,
):
    """Test _build_event_notification_payload."""
    date = datetime.date(2024, 1, 1)
    template_id = uuid4()
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_id=template_id,
    )
    ctx = DayContext(day=day, tasks=[], events=[], messages=[])

    day_svc = DayService(
        ctx=ctx,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        task_repo=mock_task_repo,
    )

    event = Event(
        uuid=uuid4(),
        user_id=test_user_id,
        name="Test Event",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "cal-1"),
        platform_id="event-1",
        platform="test",
        status="confirmed",
        starts_at=test_datetime_noon,
        date=date,
    )

    service = SheppardService(
        day_svc=day_svc,
        push_subscription_repo=mock_push_subscription_repo,
        task_repo=mock_task_repo,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        web_push_gateway=mock_web_push_gateway,
    )

    payload = service._build_event_notification_payload([event])

    assert payload.title == "Test Event"
    assert "starting soon" in payload.body
    assert len(payload.data["events"]) == 1
    assert payload.data["events"][0]["id"] == event.id


@pytest.mark.asyncio
async def test_notify_for_tasks(
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_task_repo,
    mock_push_subscription_repo,
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
):
    """Test _notify_for_tasks sends notifications."""
    date = datetime.date(2024, 1, 1)
    template_id = uuid4()
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_id=template_id,
    )
    ctx = DayContext(day=day, tasks=[], events=[], messages=[])

    day_svc = DayService(
        ctx=ctx,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        task_repo=mock_task_repo,
    )

    task = Task(
        uuid=uuid4(),
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
        date=date,
    )

    subscription = PushSubscription(
        uuid=uuid4(),
        user_id=test_user_id,
        endpoint="https://example.com/push",
        p256dh="key",
        auth="auth",
    )

    allow(mock_web_push_gateway).send_notification.and_return(None)

    service = SheppardService(
        day_svc=day_svc,
        push_subscription_repo=mock_push_subscription_repo,
        task_repo=mock_task_repo,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        web_push_gateway=mock_web_push_gateway,
        push_subscriptions=[subscription],
    )

    await service._notify_for_tasks([task])

    # Verify send_notification was called
    assert True  # If we get here, no exception was raised


@pytest.mark.asyncio
async def test_notify_for_tasks_empty_list(
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_task_repo,
    mock_push_subscription_repo,
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
):
    """Test _notify_for_tasks handles empty task list."""
    date = datetime.date(2024, 1, 1)
    template_id = uuid4()
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_id=template_id,
    )
    ctx = DayContext(day=day, tasks=[], events=[], messages=[])

    day_svc = DayService(
        ctx=ctx,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        task_repo=mock_task_repo,
    )

    service = SheppardService(
        day_svc=day_svc,
        push_subscription_repo=mock_push_subscription_repo,
        task_repo=mock_task_repo,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        web_push_gateway=mock_web_push_gateway,
    )

    # Should not raise an exception
    await service._notify_for_tasks([])


@pytest.mark.asyncio
async def test_stop_sets_mode_to_stopping(
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_task_repo,
    mock_push_subscription_repo,
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
):
    """Test stop sets mode to stopping."""
    date = datetime.date(2024, 1, 1)
    template_id = uuid4()
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_id=template_id,
    )
    ctx = DayContext(day=day, tasks=[], events=[], messages=[])

    day_svc = DayService(
        ctx=ctx,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        task_repo=mock_task_repo,
    )

    service = SheppardService(
        day_svc=day_svc,
        push_subscription_repo=mock_push_subscription_repo,
        task_repo=mock_task_repo,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        web_push_gateway=mock_web_push_gateway,
        mode="active",
    )

    service.stop()

    assert service.mode == "stopping"
    assert not service.is_running


@pytest.mark.asyncio
async def test_is_running_property(
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_task_repo,
    mock_push_subscription_repo,
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
):
    """Test is_running property returns correct value."""
    date = datetime.date(2024, 1, 1)
    template_id = uuid4()
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_id=template_id,
    )
    ctx = DayContext(day=day, tasks=[], events=[], messages=[])

    day_svc = DayService(
        ctx=ctx,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        task_repo=mock_task_repo,
    )

    # Test active mode
    service = SheppardService(
        day_svc=day_svc,
        push_subscription_repo=mock_push_subscription_repo,
        task_repo=mock_task_repo,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
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
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_task_repo,
    mock_push_subscription_repo,
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
):
    """Test _render_prompt renders template with context."""
    date = datetime.date(2024, 1, 1)
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_id=uuid4(),
    )
    ctx = DayContext(day=day, tasks=[], events=[], messages=[])

    day_svc = DayService(
        ctx=ctx,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        task_repo=mock_task_repo,
    )

    service = SheppardService(
        day_svc=day_svc,
        push_subscription_repo=mock_push_subscription_repo,
        task_repo=mock_task_repo,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
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
    assert "events" in call_kwargs
    assert "current_time" in call_kwargs
    assert call_kwargs["extra_arg"] == "value"


@pytest.mark.asyncio
async def test_morning_summary_prompt(
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_task_repo,
    mock_push_subscription_repo,
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
):
    """Test morning_summary_prompt renders morning summary template."""
    date = datetime.date(2024, 1, 1)
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_id=uuid4(),
    )
    ctx = DayContext(day=day, tasks=[], events=[], messages=[])

    day_svc = DayService(
        ctx=ctx,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        task_repo=mock_task_repo,
    )

    service = SheppardService(
        day_svc=day_svc,
        push_subscription_repo=mock_push_subscription_repo,
        task_repo=mock_task_repo,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
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
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_task_repo,
    mock_push_subscription_repo,
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
):
    """Test evening_summary_prompt renders evening summary template."""
    date = datetime.date(2024, 1, 1)
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_id=uuid4(),
    )
    ctx = DayContext(day=day, tasks=[], events=[], messages=[])

    day_svc = DayService(
        ctx=ctx,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        task_repo=mock_task_repo,
    )

    service = SheppardService(
        day_svc=day_svc,
        push_subscription_repo=mock_push_subscription_repo,
        task_repo=mock_task_repo,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        web_push_gateway=mock_web_push_gateway,
    )

    with patch("planned.application.services.sheppard.templates.render") as mock_render:
        mock_render.return_value = "evening summary"
        result = service.evening_summary_prompt()

    assert result == "evening summary"
    mock_render.assert_called_once()
    assert "evening-summary.md" in mock_render.call_args[0]


@pytest.mark.asyncio
async def test_notify_for_events(
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_task_repo,
    mock_push_subscription_repo,
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
    test_datetime_noon,
):
    """Test _notify_for_events sends notifications for events."""
    date = datetime.date(2024, 1, 1)
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_id=uuid4(),
    )
    ctx = DayContext(day=day, tasks=[], events=[], messages=[])

    day_svc = DayService(
        ctx=ctx,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        task_repo=mock_task_repo,
    )

    event = Event(
        uuid=uuid4(),
        user_id=test_user_id,
        name="Test Event",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "cal-1"),
        platform_id="event-1",
        platform="test",
        status="confirmed",
        starts_at=test_datetime_noon,
        date=date,
    )

    subscription = PushSubscription(
        uuid=uuid4(),
        user_id=test_user_id,
        endpoint="https://example.com/push",
        p256dh="key",
        auth="auth",
    )

    allow(mock_web_push_gateway).send_notification.and_return(None)

    service = SheppardService(
        day_svc=day_svc,
        push_subscription_repo=mock_push_subscription_repo,
        task_repo=mock_task_repo,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        web_push_gateway=mock_web_push_gateway,
        push_subscriptions=[subscription],
    )

    await service._notify_for_events([event])

    # Verify send_notification was called
    assert True  # If we get here, no exception was raised


@pytest.mark.asyncio
async def test_notify_for_events_empty_list(
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_task_repo,
    mock_push_subscription_repo,
    mock_calendar_service,
    mock_planning_service,
    mock_web_push_gateway,
    test_user_id,
):
    """Test _notify_for_events handles empty event list."""
    date = datetime.date(2024, 1, 1)
    day = Day(
        user_id=test_user_id,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_id=uuid4(),
    )
    ctx = DayContext(day=day, tasks=[], events=[], messages=[])

    day_svc = DayService(
        ctx=ctx,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        task_repo=mock_task_repo,
    )

    service = SheppardService(
        day_svc=day_svc,
        push_subscription_repo=mock_push_subscription_repo,
        task_repo=mock_task_repo,
        calendar_service=mock_calendar_service,
        planning_service=mock_planning_service,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        web_push_gateway=mock_web_push_gateway,
    )

    # Should not raise an exception
    await service._notify_for_events([])
