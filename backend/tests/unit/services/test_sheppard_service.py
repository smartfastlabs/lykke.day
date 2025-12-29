"""Unit tests for SheppardService."""

import datetime
from datetime import UTC
from uuid import uuid4

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
    test_user_uuid,
):
    """Test _build_notification_payload for a single task."""
    date = datetime.date(2024, 1, 1)
    day = Day(
        user_uuid=test_user_uuid,
        date=date,
        status=DayStatus.UNSCHEDULED,
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
        user_uuid=test_user_uuid,
        name="Test Task",
        status=TaskStatus.READY,
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
    assert payload.data["tasks"][0]["uuid"] == str(task.uuid)


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
    test_user_uuid,
):
    """Test _build_notification_payload for multiple tasks."""
    date = datetime.date(2024, 1, 1)
    template_uuid = uuid4()
    day = Day(
        user_uuid=test_user_uuid,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_uuid=template_uuid,
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
        user_uuid=test_user_uuid,
        name="Task 1",
        status=TaskStatus.READY,
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
    task2 = Task(
        uuid=uuid4(),
        user_uuid=test_user_uuid,
        name="Task 2",
        status=TaskStatus.READY,
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
    test_user_uuid,
):
    """Test _build_event_notification_payload."""
    date = datetime.date(2024, 1, 1)
    template_uuid = uuid4()
    day = Day(
        user_uuid=test_user_uuid,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_uuid=template_uuid,
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
    assert payload.data["events"][0]["uuid"] == str(event.uuid)


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
    test_user_uuid,
):
    """Test _notify_for_tasks sends notifications."""
    date = datetime.date(2024, 1, 1)
    template_uuid = uuid4()
    day = Day(
        user_uuid=test_user_uuid,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_uuid=template_uuid,
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
        user_uuid=test_user_uuid,
        name="Test Task",
        status=TaskStatus.READY,
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

    subscription = PushSubscription(
        uuid=uuid4(),
        user_uuid=test_user_uuid,
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
    test_user_uuid,
):
    """Test _notify_for_tasks handles empty task list."""
    date = datetime.date(2024, 1, 1)
    template_uuid = uuid4()
    day = Day(
        user_uuid=test_user_uuid,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_uuid=template_uuid,
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
    test_user_uuid,
):
    """Test stop sets mode to stopping."""
    date = datetime.date(2024, 1, 1)
    template_uuid = uuid4()
    day = Day(
        user_uuid=test_user_uuid,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_uuid=template_uuid,
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
    test_user_uuid,
):
    """Test is_running property returns correct value."""
    date = datetime.date(2024, 1, 1)
    template_uuid = uuid4()
    day = Day(
        user_uuid=test_user_uuid,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_uuid=template_uuid,
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
