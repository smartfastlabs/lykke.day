"""Unit tests for ScheduleDayHandler."""

from datetime import date as dt_date, time
from uuid import UUID, uuid4

import pytest

from lykke.application.commands.day import ScheduleDayCommand, ScheduleDayHandler
from lykke.application.queries.preview_day import PreviewDayHandler, PreviewDayQuery
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import (
    DayEntity,
    DayTemplateEntity,
    TaskEntity,
    TimeBlockDefinitionEntity,
)
from lykke.domain.value_objects.time_block import TimeBlockCategory, TimeBlockType


class _FakeDayTemplateReadOnlyRepo:
    """Fake day template repository for testing."""

    def __init__(self, template: DayTemplateEntity) -> None:
        self._template = template

    async def get(self, template_id):
        if template_id == self._template.id:
            return self._template
        raise ValueError(f"Template {template_id} not found")


class _FakeDayReadOnlyRepo:
    """Fake day repository for testing."""

    def __init__(self, day: DayEntity | None = None) -> None:
        self._day = day

    async def get(self, day_id):
        if self._day and day_id == self._day.id:
            return self._day
        raise NotFoundError(f"Day {day_id} not found")


class _FakeTaskReadOnlyRepo:
    """Fake task repository for testing."""

    def __init__(self, tasks: list[TaskEntity]) -> None:
        self._tasks = tasks

    async def search(self, query):
        return [task for task in self._tasks if task.scheduled_date == query.date]


class _FakeCalendarEntryReadOnlyRepo:
    """Fake calendar entry repository for testing."""

    def __init__(self, entries: list[object]) -> None:
        self._entries = entries

    async def search(self, query):
        return self._entries


class _FakeTimeBlockDefinitionReadOnlyRepo:
    """Fake time block definition repository for testing."""

    def __init__(self, definitions: dict[UUID, TimeBlockDefinitionEntity]) -> None:
        self._definitions = definitions

    async def get(self, def_id: UUID) -> TimeBlockDefinitionEntity:
        if def_id in self._definitions:
            return self._definitions[def_id]
        raise NotFoundError(f"TimeBlockDefinition {def_id} not found")


class _FakeReadOnlyRepos:
    """Lightweight container matching ReadOnlyRepositories protocol."""

    def __init__(
        self,
        day_template_repo: _FakeDayTemplateReadOnlyRepo,
        day_repo: _FakeDayReadOnlyRepo,
        task_repo: _FakeTaskReadOnlyRepo,
        calendar_entry_repo: _FakeCalendarEntryReadOnlyRepo,
        time_block_definition_repo: _FakeTimeBlockDefinitionReadOnlyRepo | None = None,
    ) -> None:
        fake = object()
        self.audit_log_ro_repo = fake
        self.auth_token_ro_repo = fake
        self.bot_personality_ro_repo = fake
        self.calendar_entry_ro_repo = calendar_entry_repo
        self.calendar_entry_series_ro_repo = fake
        self.calendar_ro_repo = fake
        self.conversation_ro_repo = fake
        self.day_ro_repo = day_repo
        self.day_template_ro_repo = day_template_repo
        self.factoid_ro_repo = fake
        self.message_ro_repo = fake
        self.push_subscription_ro_repo = fake
        self.routine_ro_repo = fake
        self.task_definition_ro_repo = fake
        self.task_ro_repo = task_repo
        self.time_block_definition_ro_repo = (
            time_block_definition_repo if time_block_definition_repo else fake
        )
        self.user_ro_repo = fake


class _FakeUoW:
    """Minimal UnitOfWork that collects created and added entities."""

    def __init__(
        self,
        day_template_repo: _FakeDayTemplateReadOnlyRepo,
        day_repo: _FakeDayReadOnlyRepo,
        task_repo: _FakeTaskReadOnlyRepo,
        calendar_entry_repo: _FakeCalendarEntryReadOnlyRepo,
        time_block_definition_repo: _FakeTimeBlockDefinitionReadOnlyRepo | None = None,
    ) -> None:
        fake = object()
        self.created_entities = []
        self.added = []
        self.bulk_deleted_tasks = []
        self.day_ro_repo = day_repo
        self.day_template_ro_repo = day_template_repo
        self.task_ro_repo = task_repo
        self.calendar_entry_ro_repo = calendar_entry_repo
        self.time_block_definition_ro_repo = (
            time_block_definition_repo if time_block_definition_repo else fake
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def create(self, entity):
        self.created_entities.append(entity)
        entity.create()
        return entity

    def add(self, entity):
        self.added.append(entity)
        return entity

    async def bulk_delete_tasks(self, query):
        self.bulk_deleted_tasks.append(query)


class _FakeUoWFactory:
    def __init__(
        self,
        day_template_repo: _FakeDayTemplateReadOnlyRepo,
        day_repo: _FakeDayReadOnlyRepo,
        task_repo: _FakeTaskReadOnlyRepo,
        calendar_entry_repo: _FakeCalendarEntryReadOnlyRepo,
        time_block_definition_repo: _FakeTimeBlockDefinitionReadOnlyRepo | None = None,
    ) -> None:
        self.uow = _FakeUoW(
            day_template_repo,
            day_repo,
            task_repo,
            calendar_entry_repo,
            time_block_definition_repo,
        )

    def create(self, _user_id):
        return self.uow


class _FakePreviewDayHandler:
    """Fake preview day handler for testing."""

    def __init__(self, day: DayEntity, tasks: list[TaskEntity]) -> None:
        self._day = day
        self._tasks = tasks

    async def preview_day(self, date, template_id=None):
        return value_objects.DayContext(
            day=self._day,
            tasks=self._tasks,
            calendar_entries=[],
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
        day_template_repo, day_repo, task_repo, calendar_entry_repo
    )
    uow_factory = _FakeUoWFactory(
        day_template_repo, day_repo, task_repo, calendar_entry_repo
    )
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
        day_template_repo, day_repo, task_repo, calendar_entry_repo
    )
    uow_factory = _FakeUoWFactory(
        day_template_repo, day_repo, task_repo, calendar_entry_repo
    )
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
        day_template_repo, day_repo, task_repo, calendar_entry_repo
    )
    uow_factory = _FakeUoWFactory(
        day_template_repo, day_repo, task_repo, calendar_entry_repo
    )
    preview_handler = _FakePreviewDayHandler(day, [])

    handler = ScheduleDayHandler(ro_repos, uow_factory, user_id, preview_handler)

    # Act
    await handler.handle(ScheduleDayCommand(date=task_date, template_id=template.id))

    # Assert - bulk delete should have been called
    assert len(uow_factory.uow.bulk_deleted_tasks) == 1
    delete_query = uow_factory.uow.bulk_deleted_tasks[0]
    assert delete_query.date == task_date


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
        day_template_repo, day_repo, task_repo, calendar_entry_repo
    )
    uow_factory = _FakeUoWFactory(
        day_template_repo, day_repo, task_repo, calendar_entry_repo
    )
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
        day_template_repo, day_repo, task_repo, calendar_entry_repo
    )
    uow_factory = _FakeUoWFactory(
        day_template_repo, day_repo, task_repo, calendar_entry_repo
    )
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
        day_template_repo,
        day_repo,
        task_repo,
        calendar_entry_repo,
        time_block_def_repo,
    )
    uow_factory = _FakeUoWFactory(
        day_template_repo,
        day_repo,
        task_repo,
        calendar_entry_repo,
        time_block_def_repo,
    )
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
