"""Unit tests for RecordTaskActionHandler."""

from datetime import date as dt_date
from uuid import uuid4

import pytest

from lykke.application.commands.task import RecordTaskActionCommand, RecordTaskActionHandler
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import (
    DayEntity,
    DayTemplateEntity,
    TaskEntity,
    UserEntity,
)
from lykke.domain.events.task_events import TaskActionRecordedEvent, TaskStateUpdatedEvent


class _FakeTaskReadOnlyRepo:
    """Fake task repository for testing."""

    def __init__(self, task: TaskEntity) -> None:
        self._task = task

    async def get(self, task_id):
        if task_id == self._task.id:
            return self._task
        raise NotFoundError(f"Task {task_id} not found")


class _FakeDayReadOnlyRepo:
    """Fake day repository for testing."""

    def __init__(self, day: DayEntity | None = None) -> None:
        self._day = day

    async def get(self, day_id):
        if self._day and day_id == self._day.id:
            return self._day
        raise NotFoundError(f"Day {day_id} not found")


class _FakeDayTemplateReadOnlyRepo:
    """Fake day template repository for testing."""

    def __init__(self, template: DayTemplateEntity) -> None:
        self._template = template

    async def get(self, _template_id):
        return self._template

    async def search_one(self, query):
        return self._template


class _FakeUserReadOnlyRepo:
    """Fake user repository for testing."""

    def __init__(self, user: UserEntity) -> None:
        self._user = user

    async def get(self, _user_id):
        return self._user


class _FakeReadOnlyRepos:
    """Lightweight container matching ReadOnlyRepositories protocol."""

    def __init__(
        self,
        task_repo: _FakeTaskReadOnlyRepo,
        day_repo: _FakeDayReadOnlyRepo,
        day_template_repo: _FakeDayTemplateReadOnlyRepo,
        user_repo: _FakeUserReadOnlyRepo,
    ) -> None:
        fake = object()
        self.audit_log_ro_repo = fake
        self.auth_token_ro_repo = fake
        self.bot_personality_ro_repo = fake
        self.calendar_entry_ro_repo = fake
        self.calendar_entry_series_ro_repo = fake
        self.calendar_ro_repo = fake
        self.conversation_ro_repo = fake
        self.day_ro_repo = day_repo
        self.day_template_ro_repo = day_template_repo
        self.factoid_ro_repo = fake
        self.message_ro_repo = fake
        self.notification_ro_repo = fake
        self.push_notification_ro_repo = fake
        self.push_subscription_ro_repo = fake
        self.routine_ro_repo = fake
        self.task_definition_ro_repo = fake
        self.task_ro_repo = task_repo
        self.template_ro_repo = fake
        self.time_block_definition_ro_repo = fake
        self.usecase_config_ro_repo = fake
        self.user_ro_repo = user_repo


class _FakeUoW:
    """Minimal UnitOfWork that just collects added entities."""

    def __init__(
        self, task_repo, day_repo, day_template_repo, user_repo, created_entities=None
    ) -> None:
        self.added = []
        self.created = created_entities or []
        self.task_ro_repo = task_repo
        self.day_ro_repo = day_repo
        self.day_template_ro_repo = day_template_repo
        self.user_ro_repo = user_repo

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    def add(self, entity):
        self.added.append(entity)
        return entity

    async def create(self, entity):
        self.created.append(entity)
        entity.create()
        return entity


class _FakeUoWFactory:
    def __init__(self, task_repo, day_repo, day_template_repo, user_repo) -> None:
        self.uow = _FakeUoW(task_repo, day_repo, day_template_repo, user_repo)

    def create(self, _user_id):
        return self.uow


@pytest.mark.asyncio
async def test_record_task_action_adds_task_and_day_to_uow():
    """Verify task and day are added to UoW after recording action."""
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

    task = TaskEntity(
        id=uuid4(),
        user_id=user_id,
        scheduled_date=task_date,
        name="Test Task",
        status=value_objects.TaskStatus.READY,
        type=value_objects.TaskType.WORK,
        category=value_objects.TaskCategory.WORK,
        frequency=value_objects.TaskFrequency.ONCE,
    )

    # Setup repositories
    task_repo = _FakeTaskReadOnlyRepo(task)
    day_repo = _FakeDayReadOnlyRepo(day)
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = _FakeUserReadOnlyRepo(user)

    ro_repos = _FakeReadOnlyRepos(task_repo, day_repo, day_template_repo, user_repo)
    uow_factory = _FakeUoWFactory(task_repo, day_repo, day_template_repo, user_repo)
    handler = RecordTaskActionHandler(ro_repos, uow_factory, user_id)

    # Create action
    action = value_objects.Action(
        type=value_objects.ActionType.COMPLETE,
    )

    # Act
    result = await handler.handle(RecordTaskActionCommand(task_id=task.id, action=action))

    # Assert
    assert result.status == value_objects.TaskStatus.COMPLETE
    assert len(result.actions) == 1
    assert result.actions[0].type == value_objects.ActionType.COMPLETE

    # Verify both day and task were added to UoW
    assert len(uow_factory.uow.added) == 2
    added_entities = uow_factory.uow.added
    assert any(isinstance(e, DayEntity) for e in added_entities)
    assert any(isinstance(e, TaskEntity) for e in added_entities)

    # Verify audit logs are no longer manually created
    # (They are now automatically created by the UOW when processing entities with audited events)
    assert len(uow_factory.uow.created) == 0


@pytest.mark.asyncio
async def test_record_task_action_raises_domain_events():
    """Verify domain events are raised when recording action."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)

    task = TaskEntity(
        id=uuid4(),
        user_id=user_id,
        scheduled_date=task_date,
        name="Test Task",
        status=value_objects.TaskStatus.READY,
        type=value_objects.TaskType.WORK,
        category=value_objects.TaskCategory.WORK,
        frequency=value_objects.TaskFrequency.ONCE,
    )

    task_repo = _FakeTaskReadOnlyRepo(task)
    day_repo = _FakeDayReadOnlyRepo(day)
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = _FakeUserReadOnlyRepo(user)

    ro_repos = _FakeReadOnlyRepos(task_repo, day_repo, day_template_repo, user_repo)
    uow_factory = _FakeUoWFactory(task_repo, day_repo, day_template_repo, user_repo)
    handler = RecordTaskActionHandler(ro_repos, uow_factory, user_id)

    action = value_objects.Action(
        type=value_objects.ActionType.COMPLETE,
    )

    # Act
    result = await handler.handle(RecordTaskActionCommand(task_id=task.id, action=action))

    # Assert - check that task has domain events
    task_events = [e for e in result._domain_events if isinstance(e, TaskStateUpdatedEvent)]
    assert len(task_events) > 0

    # Check day has domain events
    day_from_uow = [e for e in uow_factory.uow.added if isinstance(e, DayEntity)][0]
    day_events = [
        e for e in day_from_uow._domain_events if isinstance(e, TaskActionRecordedEvent)
    ]
    assert len(day_events) > 0


@pytest.mark.asyncio
async def test_record_task_action_raises_if_day_missing():
    """Verify error is raised if day doesn't exist when recording action."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    task = TaskEntity(
        id=uuid4(),
        user_id=user_id,
        scheduled_date=task_date,
        name="Test Task",
        status=value_objects.TaskStatus.READY,
        type=value_objects.TaskType.WORK,
        category=value_objects.TaskCategory.WORK,
        frequency=value_objects.TaskFrequency.ONCE,
    )

    task_repo = _FakeTaskReadOnlyRepo(task)
    day_repo = _FakeDayReadOnlyRepo(None)  # Day doesn't exist
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = _FakeUserReadOnlyRepo(user)

    ro_repos = _FakeReadOnlyRepos(task_repo, day_repo, day_template_repo, user_repo)
    uow_factory = _FakeUoWFactory(task_repo, day_repo, day_template_repo, user_repo)
    handler = RecordTaskActionHandler(ro_repos, uow_factory, user_id)

    action = value_objects.Action(
        type=value_objects.ActionType.COMPLETE,
    )

    # Act / Assert
    with pytest.raises(NotFoundError, match="Day"):
        await handler.handle(RecordTaskActionCommand(task_id=task.id, action=action))


@pytest.mark.asyncio
async def test_record_task_action_punt_updates_status():
    """Verify punting a task updates its status correctly."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)

    task = TaskEntity(
        id=uuid4(),
        user_id=user_id,
        scheduled_date=task_date,
        name="Test Task",
        status=value_objects.TaskStatus.READY,
        type=value_objects.TaskType.WORK,
        category=value_objects.TaskCategory.WORK,
        frequency=value_objects.TaskFrequency.ONCE,
    )

    task_repo = _FakeTaskReadOnlyRepo(task)
    day_repo = _FakeDayReadOnlyRepo(day)
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = _FakeUserReadOnlyRepo(user)

    ro_repos = _FakeReadOnlyRepos(task_repo, day_repo, day_template_repo, user_repo)
    uow_factory = _FakeUoWFactory(task_repo, day_repo, day_template_repo, user_repo)
    handler = RecordTaskActionHandler(ro_repos, uow_factory, user_id)

    action = value_objects.Action(
        type=value_objects.ActionType.PUNT,
    )

    # Act
    result = await handler.handle(RecordTaskActionCommand(task_id=task.id, action=action))

    # Assert
    assert result.status == value_objects.TaskStatus.PUNT
    assert len(result.actions) == 1
    assert result.actions[0].type == value_objects.ActionType.PUNT
    assert result.completed_at is None  # Punt doesn't set completed_at

    # Verify audit logs are no longer manually created
    # (They are now automatically created by the UOW when processing entities with audited events)
    assert len(uow_factory.uow.created) == 0
