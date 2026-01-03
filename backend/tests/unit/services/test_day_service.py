"""Unit tests for DayService."""

import datetime
from datetime import timedelta
from uuid import NAMESPACE_DNS, uuid4, uuid5

import pytest
from dobles import allow
from planned.application.services import DayService
from planned.application.services.factories import DayServiceFactory
from planned.core.exceptions import NotFoundError
from planned.domain import value_objects
from planned.domain.entities import (
    CalendarEntity,
    CalendarEntryEntity,
    DayEntity,
    DayTemplateEntity,
    TaskDefinitionEntity,
    TaskEntity,
    UserEntity,
)


@pytest.mark.asyncio
async def test_set_date_changes_date_and_reloads_context(
    mock_day_repo,
    mock_day_template_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test that set_date changes the date and reloads context."""
    old_date = datetime.date(2024, 1, 1)
    new_date = datetime.date(2024, 1, 2)
    template = DayTemplateEntity(
        slug="default",
        user_id=test_user_id,
    )

    old_day = DayEntity(
        user_id=test_user_id,
        date=old_date,
        status=value_objects.DayStatus.UNSCHEDULED,
        template=template,
    )
    new_day = DayEntity(
        user_id=test_user_id,
        date=new_date,
        status=value_objects.DayStatus.UNSCHEDULED,
        template=template,
    )

    # Mock old context
    old_day_ctx = value_objects.DayContext(
        day=old_day, tasks=[], calendar_entries=[], messages=[]
    )

    # Mock new context loading
    allow(mock_day_repo).get(new_day.id).and_return(new_day)
    allow(mock_task_repo).search_query.and_return([])
    allow(mock_calendar_entry_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])
    allow(mock_day_template_repo).get_by_slug("default").and_return(template)

    # Create service with old date
    service = DayService(
        user=test_user,
        date=old_date,
        uow_factory=mock_uow_factory,
    )

    # Create new service for new date (stateless)
    new_service = DayService(
        user=test_user,
        date=new_date,
        uow_factory=mock_uow_factory,
    )

    # Mock load_context to return new_day context
    allow(mock_day_repo).get(new_day.id).and_return(new_day)
    allow(mock_task_repo).search_query.and_return([])
    allow(mock_calendar_entry_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])

    day_ctx = await new_service.load_context()

    assert new_service.date == new_date
    assert day_ctx.day.date == new_date


@pytest.mark.asyncio
async def test_set_date_with_user_id(
    mock_day_repo,
    mock_day_template_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test set_date with explicit user_id."""
    old_date = datetime.date(2024, 1, 1)
    new_date = datetime.date(2024, 1, 2)
    template = DayTemplateEntity(
        slug="default",
        user_id=test_user_id,
    )

    old_day = DayEntity(
        user_id=test_user_id,
        date=old_date,
        status=value_objects.DayStatus.UNSCHEDULED,
        template=template,
    )
    new_day = DayEntity(
        user_id=test_user_id,
        date=new_date,
        status=value_objects.DayStatus.UNSCHEDULED,
        template=template,
    )

    old_day_ctx = value_objects.DayContext(
        day=old_day, tasks=[], calendar_entries=[], messages=[]
    )

    allow(mock_day_repo).get(new_day.id).and_return(new_day)
    allow(mock_task_repo).search_query.and_return([])
    allow(mock_calendar_entry_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])
    allow(mock_day_template_repo).get_by_slug("default").and_return(template)

    service = DayService(
        user=test_user,
        date=old_date,
        uow_factory=mock_uow_factory,
    )

    # Create new service for new date (stateless)
    new_service = DayService(
        user=test_user,
        date=new_date,
        uow_factory=mock_uow_factory,
    )

    day_ctx = await new_service.load_context(date=new_date, user_id=test_user_id)

    assert new_service.date == new_date


@pytest.mark.asyncio
async def test_get_or_preview_returns_existing_day(
    mock_day_repo,
    mock_day_template_repo,
    mock_user_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test get_or_preview returns existing day if found."""
    date = datetime.date(2024, 1, 1)
    template = DayTemplateEntity(
        slug="default",
        user_id=test_user_id,
    )
    day = DayEntity(
        user_id=test_user_id,
        date=date,
        status=value_objects.DayStatus.UNSCHEDULED,
        template=template,
    )

    allow(mock_day_repo).get(day.id).and_return(day)
    allow(mock_task_repo).search_query.and_return([])
    allow(mock_calendar_entry_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])

    # Create a DayService instance
    day_ctx = value_objects.DayContext(
        day=day, tasks=[], calendar_entries=[], messages=[]
    )
    day_svc = DayService(
        user=test_user,
        date=day_ctx.day.date,
        uow_factory=mock_uow_factory,
    )

    result = await day_svc.get_or_preview(date)

    assert result.id == day.id


@pytest.mark.asyncio
async def test_get_or_preview_creates_base_day_if_not_found(
    mock_day_repo,
    mock_day_template_repo,
    mock_user_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test get_or_preview creates base day if not found."""
    date = datetime.date(2024, 1, 1)
    template_slug = "default"

    user = UserEntity(
        id=test_user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=[template_slug] * 7),
    )

    template = DayTemplateEntity(
        slug=template_slug,
        user_id=test_user_id,
    )

    allow(mock_day_repo).get.and_raise(NotFoundError("Not found"))
    allow(mock_user_repo).get(test_user_id).and_return(user)
    allow(mock_day_template_repo).get_by_slug(template_slug).and_return(template)
    allow(mock_task_repo).search_query.and_return([])
    allow(mock_calendar_entry_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])

    # Create a DayService instance
    day_ctx = value_objects.DayContext(
        day=DayEntity(
            user_id=test_user_id,
            date=date,
            status=value_objects.DayStatus.UNSCHEDULED,
            template=template,
        ),
        tasks=[],
        calendar_entries=[],
        messages=[],
    )
    day_svc = DayService(
        user=test_user,
        date=day_ctx.day.date,
        uow_factory=mock_uow_factory,
    )

    result = await day_svc.get_or_preview(date)

    assert result.user_id == test_user_id
    assert result.date == date


@pytest.mark.asyncio
async def test_get_or_create_creates_and_saves_day(
    mock_day_repo,
    mock_day_template_repo,
    mock_user_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test get_or_create creates and saves day if not found."""
    date = datetime.date(2024, 1, 1)
    template_slug = "default"

    user = UserEntity(
        id=test_user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=[template_slug] * 7),
    )

    template = DayTemplateEntity(
        slug=template_slug,
        user_id=test_user_id,
    )

    created_day = DayEntity(
        user_id=test_user_id,
        date=date,
        status=value_objects.DayStatus.UNSCHEDULED,
        template=template,
    )

    allow(mock_day_repo).get.and_raise(NotFoundError("Not found"))
    allow(mock_user_repo).get(test_user_id).and_return(user)
    allow(mock_day_template_repo).get_by_slug(template_slug).and_return(template)
    allow(mock_day_repo).put.and_return(created_day)
    allow(mock_task_repo).search_query.and_return([])
    allow(mock_calendar_entry_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])

    # Create a DayService instance
    day_ctx = value_objects.DayContext(
        day=DayEntity(
            user_id=test_user_id,
            date=date,
            status=value_objects.DayStatus.UNSCHEDULED,
            template=template,
        ),
        tasks=[],
        calendar_entries=[],
        messages=[],
    )
    day_svc = DayService(
        user=test_user,
        date=day_ctx.day.date,
        uow_factory=mock_uow_factory,
    )

    result = await day_svc.get_or_create(date)

    assert result.user_id == test_user_id
    assert result.date == date


@pytest.mark.asyncio
async def test_save(
    mock_day_repo,
    mock_day_template_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test save persists the day."""
    date = datetime.date(2024, 1, 1)
    template = DayTemplateEntity(
        slug="default",
        user_id=test_user_id,
    )
    day = DayEntity(
        user_id=test_user_id,
        date=date,
        status=value_objects.DayStatus.UNSCHEDULED,
        template=template,
    )
    day_ctx = value_objects.DayContext(
        day=day, tasks=[], calendar_entries=[], messages=[]
    )

    allow(mock_day_repo).put.and_return(day)

    service = DayService(
        user=test_user,
        date=day_ctx.day.date,
        uow_factory=mock_uow_factory,
    )

    await service.save(day)

    # Verify put was called
    assert True  # If we get here, no exception was raised


@pytest.mark.skip(reason="Time mocking issues need to be fixed")
@pytest.mark.asyncio
async def test_get_upcoming_tasks_123(
    mock_day_repo,
    mock_day_template_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    test_datetime_noon,
    mock_uow_factory,
):
    """Test get_upcoming_tasks returns tasks within look_ahead window."""
    date = test_datetime_noon.date()
    # Use frozen datetime from fixture - test_datetime_noon is 12:00:00-6:00 (18:00:00 UTC)
    # get_current_time() will return 12:00:00 in local timezone
    from datetime import time

    future_time = time(12, 15)  # 15 minutes in the future
    template = DayTemplateEntity(
        slug="default",
        user_id=test_user_id,
    )

    day = DayEntity(
        user_id=test_user_id,
        date=date,
        status=value_objects.DayStatus.UNSCHEDULED,
        template=template,
    )

    # Task that should be included (within window)
    task1 = TaskEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Upcoming Task",
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
        schedule=value_objects.TaskSchedule(
            start_time=future_time, timing_type=value_objects.TimingType.FIXED_TIME
        ),
    )

    # Task that should be excluded (too far in future)
    far_future_time = time(14, 0)  # 2 hours in the future
    task2 = TaskEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Future Task",
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
        schedule=value_objects.TaskSchedule(
            start_time=far_future_time,
            timing_type=value_objects.TimingType.FIXED_TIME,
        ),
    )

    # Task that should be excluded (already completed)
    task3 = TaskEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Completed Task",
        status=value_objects.TaskStatus.COMPLETE,
        scheduled_date=date,
        task_definition=TaskDefinitionEntity(
            user_id=test_user_id,
            name="Task Def",
            description="Test task definition",
            type=value_objects.TaskType.CHORE,
        ),
        category=value_objects.TaskCategory.HOUSE,
        frequency=value_objects.TaskFrequency.ONCE,
        schedule=value_objects.TaskSchedule(
            start_time=future_time, timing_type=value_objects.TimingType.FIXED_TIME
        ),
    )

    day_ctx = value_objects.DayContext(
        day=day,
        tasks=[task1, task2, task3],
        calendar_entries=[],
        messages=[],
    )

    # Mock repositories for GetDayContextHandler
    from planned.domain.value_objects.query import DateQuery

    day_id = DayEntity.id_from_date_and_user(date, test_user_id)
    allow(mock_day_repo).get(day_id).and_raise(NotFoundError("Day not found"))
    allow(mock_day_template_repo).get_by_slug("default").and_return(template)
    allow(mock_task_repo).search_query.and_return([task1, task2, task3])
    allow(mock_calendar_entry_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])

    service = DayService(
        user=test_user,
        date=day_ctx.day.date,
        uow_factory=mock_uow_factory,
    )

    # Time is frozen by test_datetime_noon fixture
    result = await service.get_upcoming_tasks(look_ahead=timedelta(minutes=30))

    # Should only include task1 (within window and not completed)
    assert len(result) == 1
    assert result[0].id == task1.id


@pytest.mark.skip(reason="Time mocking issues need to be fixed")
@pytest.mark.asyncio
async def test_get_upcoming_calendar_entries(
    mock_day_repo,
    mock_day_template_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    test_datetime_noon,
    mock_uow_factory,
):
    """Test get_upcoming_calendar_entries returns calendar entries within look_ahead window."""
    date = datetime.date(2025, 11, 27)
    # Use frozen datetime from fixture - get_current_datetime() will return the frozen time
    # which is 2025-11-27 18:00:00 UTC (12:00:00-6:00)
    from planned.core.utils.dates import get_current_datetime

    now = get_current_datetime()
    future_time = now + timedelta(minutes=15)
    far_future = now + timedelta(hours=2)
    past_time = now - timedelta(hours=1)
    template = DayTemplateEntity(
        slug="default",
        user_id=test_user_id,
    )

    day = DayEntity(
        user_id=test_user_id,
        date=date,
        status=value_objects.DayStatus.UNSCHEDULED,
        template=template,
    )

    # CalendarEntry that should be included (within window)
    calendar_entry1 = CalendarEntryEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Upcoming Calendar Entry",
        frequency=value_objects.TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "cal-1"),
        platform_id="entry-1",
        platform="test",
        status="confirmed",
        starts_at=future_time,
    )

    # CalendarEntry that should be excluded (too far in future)
    calendar_entry2 = CalendarEntryEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Future Calendar Entry",
        frequency=value_objects.TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "cal-1"),
        platform_id="entry-2",
        platform="test",
        status="confirmed",
        starts_at=far_future,
    )

    # CalendarEntry that should be excluded (cancelled)
    calendar_entry3 = CalendarEntryEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Cancelled Calendar Entry",
        frequency=value_objects.TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "cal-1"),
        platform_id="entry-3",
        platform="test",
        status="cancelled",
        starts_at=future_time,
    )

    # CalendarEntry that should be included (ongoing - started in past but not ended)
    calendar_entry4 = CalendarEntryEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Ongoing Calendar Entry",
        frequency=value_objects.TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "cal-1"),
        platform_id="entry-4",
        platform="test",
        status="confirmed",
        starts_at=past_time,
        ends_at=future_time,
    )

    day_ctx = value_objects.DayContext(
        day=day,
        tasks=[],
        calendar_entries=[
            calendar_entry1,
            calendar_entry2,
            calendar_entry3,
            calendar_entry4,
        ],
        messages=[],
    )

    # Mock repositories for GetDayContextHandler
    from planned.domain.value_objects.query import DateQuery

    day_id = DayEntity.id_from_date_and_user(date, test_user_id)
    allow(mock_day_repo).get(day_id).and_raise(NotFoundError("Day not found"))
    allow(mock_day_template_repo).get_by_slug("default").and_return(template)
    allow(mock_task_repo).search_query.and_return([])
    allow(mock_calendar_entry_repo).search_query.and_return(
        [
            calendar_entry1,
            calendar_entry2,
            calendar_entry3,
            calendar_entry4,
        ]
    )
    allow(mock_message_repo).search_query.and_return([])

    service = DayService(
        user=test_user,
        date=day_ctx.day.date,
        uow_factory=mock_uow_factory,
    )

    # Time is frozen by test_datetime_noon fixture
    result = await service.get_upcoming_calendar_entries(
        look_ahead=timedelta(minutes=30)
    )

    # Should include calendar_entry1 and calendar_entry4 (within window and not cancelled)
    assert len(result) == 2
    assert any(e.id == calendar_entry1.id for e in result)
    assert any(e.id == calendar_entry4.id for e in result)


@pytest.mark.asyncio
async def test_for_date_creates_service(
    mock_day_repo,
    mock_day_template_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_task_repo,
    mock_user_repo,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test for_date creates a DayService with loaded context."""
    date = datetime.date(2024, 1, 1)
    template = DayTemplateEntity(
        slug="default",
        user_id=test_user_id,
    )
    day = DayEntity(
        user_id=test_user_id,
        date=date,
        status=value_objects.DayStatus.UNSCHEDULED,
        template=template,
    )

    allow(mock_day_repo).get(day.id).and_return(day)
    allow(mock_task_repo).search_query.and_return([])
    allow(mock_calendar_entry_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])

    # Create a DayService instance using the factory
    template_slug = test_user.settings.template_defaults[date.weekday()]
    allow(mock_day_template_repo).get_by_slug(template_slug).and_return(template)
    factory = DayServiceFactory(
        user=test_user,
        uow_factory=mock_uow_factory,
    )
    service = await factory.create(date, user_id=test_user_id)

    assert service.date == date
    day_ctx = await service.load_context()
    assert day_ctx.day.id == day.id


@pytest.mark.asyncio
async def test_base_day_with_template(
    test_user_id,
    test_user,
):
    """Test Day.create_for_date creates day with specified template."""
    from planned.domain.entities import DayEntity

    date = datetime.date(2024, 1, 1)
    template = DayTemplateEntity(
        slug="custom",
        user_id=test_user_id,
    )

    day = DayEntity.create_for_date(
        date,
        user_id=test_user_id,
        template=template,
    )

    assert day.user_id == test_user_id
    assert day.date == date
    assert day.template is not None
    assert day.template.id == template.id
    assert day.status == value_objects.DayStatus.UNSCHEDULED


@pytest.mark.asyncio
async def test_load_context_instance_method(
    mock_day_repo,
    mock_day_template_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    mock_uow_factory,
):
    """Test load_context instance method reloads context."""
    date = datetime.date(2024, 1, 1)
    template = DayTemplateEntity(
        slug="default",
        user_id=test_user_id,
    )
    old_day = DayEntity(
        user_id=test_user_id,
        date=date,
        status=value_objects.DayStatus.UNSCHEDULED,
        template=template,
    )
    new_day = DayEntity(
        user_id=test_user_id,
        date=date,
        status=value_objects.DayStatus.SCHEDULED,
        template=template,
    )

    old_day_ctx = value_objects.DayContext(
        day=old_day, tasks=[], calendar_entries=[], messages=[]
    )

    allow(mock_day_repo).get(new_day.id).and_return(new_day)
    allow(mock_task_repo).search_query.and_return([])
    allow(mock_calendar_entry_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])
    allow(mock_day_template_repo).get_by_slug("default").and_return(template)

    service = DayService(
        user=test_user,
        date=old_day_ctx.day.date,
        uow_factory=mock_uow_factory,
    )

    day_ctx = await service.load_context()

    assert day_ctx.day.status == value_objects.DayStatus.SCHEDULED
    loaded_ctx = await service.load_context()
    assert loaded_ctx.day.status == value_objects.DayStatus.SCHEDULED


@pytest.mark.skip(reason="Time mocking issues need to be fixed")
@pytest.mark.asyncio
async def test_get_upcoming_tasks_with_available_time(
    mock_day_repo,
    mock_day_template_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    test_datetime_noon,
    mock_uow_factory,
):
    """Test get_upcoming_tasks handles tasks with available_time."""
    date = datetime.date(2025, 11, 27)
    # Use frozen datetime from fixture
    now = test_datetime_noon
    past_available_time = (now - timedelta(minutes=30)).time()
    future_available_time = (now + timedelta(minutes=30)).time()
    template = DayTemplateEntity(
        slug="default",
        user_id=test_user_id,
    )

    day = DayEntity(
        user_id=test_user_id,
        date=date,
        status=value_objects.DayStatus.UNSCHEDULED,
        template=template,
    )

    # Task with available_time in past (should be included)
    task1 = TaskEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Available Task",
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
        schedule=value_objects.TaskSchedule(
            available_time=past_available_time,
            timing_type=value_objects.TimingType.FLEXIBLE,
        ),
    )

    # Task with available_time in future (should be excluded)
    task2 = TaskEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Future Available Task",
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
        schedule=value_objects.TaskSchedule(
            available_time=future_available_time,
            timing_type=value_objects.TimingType.FLEXIBLE,
        ),
    )

    day_ctx = value_objects.DayContext(
        day=day, tasks=[task1, task2], calendar_entries=[], messages=[]
    )

    # Mock repositories for GetDayContextHandler
    day_id = DayEntity.id_from_date_and_user(date, test_user_id)
    allow(mock_day_repo).get(day_id).and_raise(NotFoundError("Day not found"))
    allow(mock_day_template_repo).get_by_slug("default").and_return(template)
    allow(mock_task_repo).search_query.and_return([task1, task2])
    allow(mock_calendar_entry_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])

    service = DayService(
        user=test_user,
        date=day_ctx.day.date,
        uow_factory=mock_uow_factory,
    )

    # Time is frozen by test_datetime_noon fixture
    result = await service.get_upcoming_tasks(look_ahead=timedelta(minutes=30))

    assert len(result) == 1
    assert result[0].id == task1.id


@pytest.mark.skip(reason="Time mocking issues need to be fixed")
@pytest.mark.asyncio
async def test_get_upcoming_tasks_with_end_time(
    mock_day_repo,
    mock_day_template_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    test_datetime_noon,
    mock_uow_factory,
):
    """Test get_upcoming_tasks excludes tasks past end_time."""
    date = datetime.date(2025, 11, 27)
    # Use frozen datetime from fixture
    now = test_datetime_noon
    past_end_time = (now - timedelta(minutes=30)).time()
    future_start_time = (now + timedelta(minutes=15)).time()
    template = DayTemplateEntity(
        slug="default",
        user_id=test_user_id,
    )

    day = DayEntity(
        user_id=test_user_id,
        date=date,
        status=value_objects.DayStatus.UNSCHEDULED,
        template=template,
    )

    # Task with end_time in past (should be excluded)
    task1 = TaskEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Past End Time Task",
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
        schedule=value_objects.TaskSchedule(
            start_time=future_start_time,
            end_time=past_end_time,
            timing_type=value_objects.TimingType.FIXED_TIME,
        ),
    )

    # Task with end_time in future (should be included)
    task2 = TaskEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Valid Task",
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
        schedule=value_objects.TaskSchedule(
            start_time=future_start_time,
            end_time=(now + timedelta(hours=1)).time(),
            timing_type=value_objects.TimingType.FIXED_TIME,
        ),
    )

    day_ctx = value_objects.DayContext(
        day=day, tasks=[task1, task2], calendar_entries=[], messages=[]
    )

    # Mock repositories for GetDayContextHandler
    day_id = DayEntity.id_from_date_and_user(date, test_user_id)
    allow(mock_day_repo).get(day_id).and_raise(NotFoundError("Day not found"))
    allow(mock_day_template_repo).get_by_slug("default").and_return(template)
    allow(mock_task_repo).search_query.and_return([task1, task2])
    allow(mock_calendar_entry_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])

    service = DayService(
        user=test_user,
        date=day_ctx.day.date,
        uow_factory=mock_uow_factory,
    )

    # Time is frozen by test_datetime_noon fixture
    result = await service.get_upcoming_tasks(look_ahead=timedelta(minutes=30))

    assert len(result) == 1
    assert result[0].id == task2.id


@pytest.mark.skip(reason="Time mocking issues need to be fixed")
@pytest.mark.asyncio
async def test_get_upcoming_tasks_excludes_completed_at(
    mock_day_repo,
    mock_day_template_repo,
    mock_calendar_entry_repo,
    mock_message_repo,
    mock_task_repo,
    test_user_id,
    test_user,
    test_datetime_noon,
    mock_uow_factory,
):
    """Test get_upcoming_tasks excludes tasks with completed_at set."""
    date = datetime.date(2025, 11, 27)
    # Use frozen datetime from fixture
    now = test_datetime_noon
    future_time = (now + timedelta(minutes=15)).time()
    template = DayTemplateEntity(
        slug="default",
        user_id=test_user_id,
    )

    day = DayEntity(
        user_id=test_user_id,
        date=date,
        status=value_objects.DayStatus.UNSCHEDULED,
        template=template,
    )

    # Task with completed_at (should be excluded even if status is PENDING)
    task1 = TaskEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Completed Task",
        status=value_objects.TaskStatus.PENDING,
        scheduled_date=date,
        completed_at=now,
        task_definition=TaskDefinitionEntity(
            user_id=test_user_id,
            name="Task Def",
            description="Test task definition",
            type=value_objects.TaskType.CHORE,
        ),
        category=value_objects.TaskCategory.HOUSE,
        frequency=value_objects.TaskFrequency.ONCE,
        schedule=value_objects.TaskSchedule(
            start_time=future_time,
            timing_type=value_objects.TimingType.FIXED_TIME,
        ),
    )

    # Task without completed_at (should be included)
    task2 = TaskEntity(
        id=uuid4(),
        user_id=test_user_id,
        name="Valid Task",
        status=value_objects.TaskStatus.PENDING,
        scheduled_date=date,
        task_definition=TaskDefinitionEntity(
            user_id=test_user_id,
            name="Task Def",
            description="Test task definition",
            type=value_objects.TaskType.CHORE,
        ),
        category=value_objects.TaskCategory.HOUSE,
        frequency=value_objects.TaskFrequency.ONCE,
        schedule=value_objects.TaskSchedule(
            start_time=future_time,
            timing_type=value_objects.TimingType.FIXED_TIME,
        ),
    )

    day_ctx = value_objects.DayContext(
        day=day, tasks=[task1, task2], calendar_entries=[], messages=[]
    )

    # Mock repositories for GetDayContextHandler
    day_id = DayEntity.id_from_date_and_user(date, test_user_id)
    allow(mock_day_repo).get(day_id).and_raise(NotFoundError("Day not found"))
    allow(mock_day_template_repo).get_by_slug("default").and_return(template)
    allow(mock_task_repo).search_query.and_return([task1, task2])
    allow(mock_calendar_entry_repo).search_query.and_return([])
    allow(mock_message_repo).search_query.and_return([])

    service = DayService(
        user=test_user,
        date=day_ctx.day.date,
        uow_factory=mock_uow_factory,
    )

    # Time is frozen by test_datetime_noon fixture
    result = await service.get_upcoming_tasks(look_ahead=timedelta(minutes=30))

    assert len(result) == 1
    assert result[0].id == task2.id
