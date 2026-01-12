"""Unit tests for ScheduleDayHandler."""

from datetime import date as dt_date
from uuid import uuid4

import pytest

from lykke.application.commands.day import ScheduleDayHandler
from lykke.application.queries.preview_day import PreviewDayHandler
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity, TaskEntity


class _FakeDayTemplateReadOnlyRepo:
    """Fake day template repository for testing."""

    def __init__(self, template: DayTemplateEntity) -> None:
        self._template = template

    async def get(self, template_id):
        if template_id == self._template.id:
            return self._template
        raise ValueError(f"Template {template_id} not found")


class _FakeReadOnlyRepos:
    """Lightweight container matching ReadOnlyRepositories protocol."""

    def __init__(self, day_template_repo: _FakeDayTemplateReadOnlyRepo) -> None:
        fake = object()
        self.auth_token_ro_repo = fake
        self.calendar_entry_ro_repo = fake
        self.calendar_entry_series_ro_repo = fake
        self.calendar_ro_repo = fake
        self.day_ro_repo = fake
        self.day_template_ro_repo = day_template_repo
        self.push_subscription_ro_repo = fake
        self.routine_ro_repo = fake
        self.task_definition_ro_repo = fake
        self.task_ro_repo = fake
        self.time_block_definition_ro_repo = fake
        self.user_ro_repo = fake


class _FakeUoW:
    """Minimal UnitOfWork that collects created and added entities."""

    def __init__(self, day_template_repo: _FakeDayTemplateReadOnlyRepo) -> None:
        self.created_entities = []
        self.added = []
        self.bulk_deleted_tasks = []
        self.day_template_ro_repo = day_template_repo

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def create(self, entity):
        self.created_entities.append(entity)
        entity.create()

    def add(self, entity):
        self.added.append(entity)

    async def bulk_delete_tasks(self, query):
        self.bulk_deleted_tasks.append(query)


class _FakeUoWFactory:
    def __init__(self, day_template_repo: _FakeDayTemplateReadOnlyRepo) -> None:
        self.uow = _FakeUoW(day_template_repo)
        self._day_template_repo = day_template_repo

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
    ro_repos = _FakeReadOnlyRepos(day_template_repo)
    uow_factory = _FakeUoWFactory(day_template_repo)
    preview_handler = _FakePreviewDayHandler(day, tasks)

    handler = ScheduleDayHandler(ro_repos, uow_factory, user_id, preview_handler)

    # Act
    result = await handler.schedule_day(task_date, template.id)

    # Assert
    assert result.day.date == task_date
    assert result.day.user_id == user_id
    assert result.day.status == value_objects.DayStatus.SCHEDULED
    assert len(result.tasks) == 2

    # Verify day was created
    assert len(uow_factory.uow.created_entities) >= 1
    created_day = [e for e in uow_factory.uow.created_entities if isinstance(e, DayEntity)][0]
    assert created_day.date == task_date

    # Verify tasks were created
    created_tasks = [e for e in uow_factory.uow.created_entities if isinstance(e, TaskEntity)]
    assert len(created_tasks) == 2


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
    ro_repos = _FakeReadOnlyRepos(day_template_repo)
    uow_factory = _FakeUoWFactory(day_template_repo)
    preview_handler = _FakePreviewDayHandler(day, [])

    handler = ScheduleDayHandler(ro_repos, uow_factory, user_id, preview_handler)

    # Act
    await handler.schedule_day(task_date, template.id)

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
    ro_repos = _FakeReadOnlyRepos(day_template_repo)
    uow_factory = _FakeUoWFactory(day_template_repo)
    preview_handler = _FakePreviewDayHandler(day, [])

    handler = ScheduleDayHandler(ro_repos, uow_factory, user_id, preview_handler)

    # Act & Assert
    with pytest.raises(ValueError, match="Day template is required to schedule"):
        await handler.schedule_day(task_date, template.id)


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
    ro_repos = _FakeReadOnlyRepos(day_template_repo)
    uow_factory = _FakeUoWFactory(day_template_repo)
    preview_handler = _FakePreviewDayHandler(day, [])

    handler = ScheduleDayHandler(ro_repos, uow_factory, user_id, preview_handler)

    # Act
    result = await handler.schedule_day(task_date, template.id)

    # Assert
    assert result.day.template == template
