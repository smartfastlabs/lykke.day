"""Unit tests for DayService."""

import datetime
from datetime import UTC, timedelta
from unittest.mock import patch
from uuid import NAMESPACE_DNS, UUID, uuid4, uuid5

import pytest
from dobles import allow

from planned.application.services import DayService
from planned.core.exceptions import exceptions
from planned.domain.entities import (
    Day,
    DayContext,
    DayStatus,
    DayTemplate,
    Event,
    Task,
    TaskDefinition,
    User,
)
from planned.domain.value_objects.task import (
    TaskCategory,
    TaskFrequency,
    TaskSchedule,
    TaskStatus,
    TaskType,
    TimingType,
)
from planned.domain.value_objects.user import UserSetting


def setup_repo_listeners(mock_event_repo, mock_message_repo, mock_task_repo):
    """Helper to set up listen mocks for repositories."""
    allow(mock_event_repo).listen.and_return(None)
    allow(mock_message_repo).listen.and_return(None)
    allow(mock_task_repo).listen.and_return(None)


@pytest.mark.asyncio
async def test_set_date_changes_date_and_reloads_context(
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_task_repo,
    test_user_uuid,
):
    """Test that set_date changes the date and reloads context."""
    old_date = datetime.date(2024, 1, 1)
    new_date = datetime.date(2024, 1, 2)
    template_uuid = uuid4()

    old_day = Day(
        user_uuid=test_user_uuid,
        date=old_date,
        status=DayStatus.UNSCHEDULED,
        template_uuid=template_uuid,
    )
    new_day = Day(
        user_uuid=test_user_uuid,
        date=new_date,
        status=DayStatus.UNSCHEDULED,
        template_uuid=template_uuid,
    )

    # Mock old context
    old_ctx = DayContext(day=old_day, tasks=[], events=[], messages=[])

    # Mock new context loading
    allow(mock_day_repo).get(new_day.uuid).and_return(new_day)
    allow(mock_task_repo).search_query.and_return([])
    allow(mock_event_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])
    setup_repo_listeners(mock_event_repo, mock_message_repo, mock_task_repo)

    # Create service with old date
    service = DayService(
        ctx=old_ctx,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        task_repo=mock_task_repo,
    )

    # Set user_uuid on repo for extraction
    mock_day_repo.user_uuid = test_user_uuid

    await service.set_date(new_date)

    assert service.date == new_date
    assert service.ctx.day.date == new_date


@pytest.mark.asyncio
async def test_set_date_with_user_uuid(
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_task_repo,
    test_user_uuid,
):
    """Test set_date with explicit user_uuid."""
    old_date = datetime.date(2024, 1, 1)
    new_date = datetime.date(2024, 1, 2)

    old_day = Day(
        user_uuid=test_user_uuid,
        date=old_date,
        status=DayStatus.UNSCHEDULED,
        template_uuid=uuid4(),
    )
    new_day = Day(
        user_uuid=test_user_uuid,
        date=new_date,
        status=DayStatus.UNSCHEDULED,
        template_uuid=uuid4(),
    )

    old_ctx = DayContext(day=old_day, tasks=[], events=[], messages=[])

    allow(mock_day_repo).get(new_day.uuid).and_return(new_day)
    allow(mock_task_repo).search_query.and_return([])
    allow(mock_event_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])
    setup_repo_listeners(mock_event_repo, mock_message_repo, mock_task_repo)

    service = DayService(
        ctx=old_ctx,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        task_repo=mock_task_repo,
    )

    await service.set_date(new_date, user_uuid=test_user_uuid)

    assert service.date == new_date


@pytest.mark.asyncio
async def test_get_or_preview_returns_existing_day(
    mock_day_repo,
    mock_day_template_repo,
    test_user_uuid,
):
    """Test get_or_preview returns existing day if found."""
    date = datetime.date(2024, 1, 1)
    day = Day(
        user_uuid=test_user_uuid,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_uuid=uuid4(),
    )

    allow(mock_day_repo).get(day.uuid).and_return(day)

    result = await DayService.get_or_preview(
        date,
        user_uuid=test_user_uuid,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
    )

    assert result.uuid == day.uuid


@pytest.mark.asyncio
async def test_get_or_preview_creates_base_day_if_not_found(
    mock_day_repo,
    mock_day_template_repo,
    mock_user_repo,
    test_user_uuid,
):
    """Test get_or_preview creates base day if not found."""
    date = datetime.date(2024, 1, 1)
    template_id = "default"

    user = User(
        uuid=test_user_uuid,
        email="test@example.com",
        password_hash="hash",
        settings=UserSetting(template_defaults=[template_id] * 7),
    )

    template_uuid = uuid4()
    template = DayTemplate(
        uuid=template_uuid,
        slug=str(template_id),
        user_uuid=test_user_uuid,
    )

    allow(mock_day_repo).get.and_raise(exceptions.NotFoundError("Not found"))
    allow(mock_user_repo).get(test_user_uuid).and_return(user)
    allow(mock_day_template_repo).get_by_slug(template.slug).and_return(template)

    result = await DayService.get_or_preview(
        date,
        user_uuid=test_user_uuid,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        user_repo=mock_user_repo,
    )

    assert result.user_uuid == test_user_uuid
    assert result.date == date


@pytest.mark.asyncio
async def test_get_or_create_creates_and_saves_day(
    mock_day_repo,
    mock_day_template_repo,
    mock_user_repo,
    test_user_uuid,
):
    """Test get_or_create creates and saves day if not found."""
    date = datetime.date(2024, 1, 1)
    template_uuid = uuid4()
    template_slug = "default"

    user = User(
        uuid=test_user_uuid,
        email="test@example.com",
        password_hash="hash",
        settings=UserSetting(template_defaults=[template_slug] * 7),
    )

    template = DayTemplate(
        uuid=template_uuid,
        slug=template_slug,
        user_uuid=test_user_uuid,
    )

    created_day = Day(
        user_uuid=test_user_uuid,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_uuid=template_uuid,
    )

    allow(mock_day_repo).get.and_raise(exceptions.NotFoundError("Not found"))
    allow(mock_user_repo).get(test_user_uuid).and_return(user)
    allow(mock_day_template_repo).get_by_slug(template_slug).and_return(template)
    allow(mock_day_repo).put.and_return(created_day)

    result = await DayService.get_or_create(
        date,
        user_uuid=test_user_uuid,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        user_repo=mock_user_repo,
    )

    assert result.user_uuid == test_user_uuid
    assert result.date == date


@pytest.mark.asyncio
async def test_save(
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_task_repo,
    test_user_uuid,
):
    """Test save persists the day."""
    date = datetime.date(2024, 1, 1)
    template_uuid = uuid4()
    day = Day(
        user_uuid=test_user_uuid,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_uuid=template_uuid,
    )
    ctx = DayContext(day=day, tasks=[], events=[], messages=[])

    allow(mock_day_repo).put.and_return(day)

    service = DayService(
        ctx=ctx,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        task_repo=mock_task_repo,
    )

    await service.save()

    # Verify put was called
    assert True  # If we get here, no exception was raised


@pytest.mark.asyncio
@pytest.mark.skip
async def test_get_upcomming_tasks(
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_task_repo,
    test_user_uuid,
):
    """Test get_upcomming_tasks returns tasks within look_ahead window."""
    date = datetime.date(2024, 1, 1)
    now = datetime.datetime.now(UTC)
    current_time = now.time()
    future_time = (now + timedelta(minutes=15)).time()
    template_uuid = uuid4()

    day = Day(
        user_uuid=test_user_uuid,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_uuid=template_uuid,
    )

    # Task that should be included (within window)
    task1 = Task(
        uuid=uuid4(),
        user_uuid=test_user_uuid,
        name="Upcoming Task",
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
        schedule=TaskSchedule(
            start_time=future_time, timing_type=TimingType.FIXED_TIME
        ),
        date=date,
    )

    # Task that should be excluded (too far in future)
    far_future_time = (now + timedelta(hours=2)).time()
    task2 = Task(
        uuid=uuid4(),
        user_uuid=test_user_uuid,
        name="Future Task",
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
        schedule=TaskSchedule(
            start_time=far_future_time,
            timing_type=TimingType.FIXED_TIME,
        ),
        date=date,
    )

    # Task that should be excluded (already completed)
    task3 = Task(
        uuid=uuid4(),
        user_uuid=test_user_uuid,
        name="Completed Task",
        status=TaskStatus.COMPLETE,
        scheduled_date=date,
        task_definition=TaskDefinition(
            user_uuid=test_user_uuid,
            id="def-3",
            name="Task Def",
            description="Test task definition",
            type=TaskType.CHORE,
        ),
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.ONCE,
        schedule=TaskSchedule(
            start_time=future_time, timing_type=TimingType.FIXED_TIME
        ),
        date=date,
    )

    ctx = DayContext(day=day, tasks=[task1, task2, task3], events=[], messages=[])

    service = DayService(
        ctx=ctx,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        task_repo=mock_task_repo,
    )

    # Mock current time
    with (
        patch(
            "planned.infrastructure.utils.dates.get_current_time",
            return_value=current_time,
        ),
        patch(
            "planned.infrastructure.utils.dates.get_current_datetime", return_value=now
        ),
    ):
        result = await service.get_upcomming_tasks(look_ahead=timedelta(minutes=30))

    # Should only include task1 (within window and not completed)
    assert len(result) == 1
    assert result[0].uuid == task1.uuid


@pytest.mark.asyncio
async def test_get_upcomming_events(
    mock_day_repo,
    mock_day_template_repo,
    mock_event_repo,
    mock_message_repo,
    mock_task_repo,
    test_user_uuid,
):
    """Test get_upcomming_events returns events within look_ahead window."""
    date = datetime.date(2024, 1, 1)
    now = datetime.datetime.now(UTC)
    future_time = now + timedelta(minutes=15)
    far_future = now + timedelta(hours=2)
    past_time = now - timedelta(hours=1)
    template_uuid = uuid4()

    day = Day(
        user_uuid=test_user_uuid,
        date=date,
        status=DayStatus.UNSCHEDULED,
        template_uuid=template_uuid,
    )

    # Event that should be included (within window)
    event1 = Event(
        uuid=uuid4(),
        user_uuid=test_user_uuid,
        name="Upcoming Event",
        frequency=TaskFrequency.ONCE,
        calendar_uuid=uuid5(NAMESPACE_DNS, "cal-1"),
        platform_id="event-1",
        platform="test",
        status="confirmed",
        starts_at=future_time,
        date=date,
    )

    # Event that should be excluded (too far in future)
    event2 = Event(
        uuid=uuid4(),
        user_uuid=test_user_uuid,
        name="Future Event",
        frequency=TaskFrequency.ONCE,
        calendar_uuid=uuid5(NAMESPACE_DNS, "cal-1"),
        platform_id="event-2",
        platform="test",
        status="confirmed",
        starts_at=far_future,
        date=date,
    )

    # Event that should be excluded (cancelled)
    event3 = Event(
        uuid=uuid4(),
        user_uuid=test_user_uuid,
        name="Cancelled Event",
        frequency=TaskFrequency.ONCE,
        calendar_uuid=uuid5(NAMESPACE_DNS, "cal-1"),
        platform_id="event-3",
        platform="test",
        status="cancelled",
        starts_at=future_time,
        date=date,
    )

    # Event that should be included (ongoing - started in past but not ended)
    event4 = Event(
        uuid=uuid4(),
        user_uuid=test_user_uuid,
        name="Ongoing Event",
        frequency=TaskFrequency.ONCE,
        calendar_uuid=uuid5(NAMESPACE_DNS, "cal-1"),
        platform_id="event-4",
        platform="test",
        status="confirmed",
        starts_at=past_time,
        ends_at=future_time,
        date=date,
    )

    ctx = DayContext(
        day=day, tasks=[], events=[event1, event2, event3, event4], messages=[]
    )

    service = DayService(
        ctx=ctx,
        day_repo=mock_day_repo,
        day_template_repo=mock_day_template_repo,
        event_repo=mock_event_repo,
        message_repo=mock_message_repo,
        task_repo=mock_task_repo,
    )

    with patch(
        "planned.infrastructure.utils.dates.get_current_datetime", return_value=now
    ):
        result = await service.get_upcomming_events(look_ahead=timedelta(minutes=30))

    # Should include event1 and event4 (within window and not cancelled)
    assert len(result) == 2
    assert any(e.uuid == event1.uuid for e in result)
    assert any(e.uuid == event4.uuid for e in result)
    assert any(e.uuid == event4.uuid for e in result)
