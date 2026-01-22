"""Unit tests for AddReminderToDayHandler."""

from datetime import date as dt_date
from uuid import uuid4

import pytest

from lykke.application.commands.day import AddReminderToDayCommand, AddReminderToDayHandler
from lykke.core.exceptions import DomainError, NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity, UserEntity
from lykke.domain.events.day_events import ReminderAddedEvent


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
        self.task_ro_repo = fake
        self.time_block_definition_ro_repo = fake
        self.usecase_config_ro_repo = fake
        self.user_ro_repo = user_repo


class _FakeUoW:
    """Minimal UnitOfWork that just collects added entities."""

    def __init__(
        self, day_repo, day_template_repo, user_repo, created_entities=None
    ) -> None:
        self.added = []
        self.created = created_entities or []
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
    def __init__(self, day_repo, day_template_repo, user_repo) -> None:
        self.uow = _FakeUoW(day_repo, day_template_repo, user_repo)

    def create(self, _user_id):
        return self.uow


@pytest.mark.asyncio
async def test_add_reminder_adds_reminder_to_existing_day():
    """Test add_reminder adds a reminder to an existing day."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)

    day_repo = _FakeDayReadOnlyRepo(day)
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = _FakeUserReadOnlyRepo(user)

    ro_repos = _FakeReadOnlyRepos(day_repo, day_template_repo, user_repo)
    uow_factory = _FakeUoWFactory(day_repo, day_template_repo, user_repo)
    handler = AddReminderToDayHandler(ro_repos, uow_factory, user_id)

    # Act
    result = await handler.handle(AddReminderToDayCommand(date=task_date, reminder="Test Reminder"))

    # Assert
    assert len(result.reminders) == 1
    assert result.reminders[0].name == "Test Reminder"
    assert result.reminders[0].status == value_objects.ReminderStatus.INCOMPLETE
    assert len(uow_factory.uow.added) == 1
    assert uow_factory.uow.added[0] == result


@pytest.mark.asyncio
async def test_add_reminder_emits_domain_event():
    """Test add_reminder emits ReminderAddedEvent."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)

    day_repo = _FakeDayReadOnlyRepo(day)
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = _FakeUserReadOnlyRepo(user)

    ro_repos = _FakeReadOnlyRepos(day_repo, day_template_repo, user_repo)
    uow_factory = _FakeUoWFactory(day_repo, day_template_repo, user_repo)
    handler = AddReminderToDayHandler(ro_repos, uow_factory, user_id)

    # Act
    result = await handler.handle(AddReminderToDayCommand(date=task_date, reminder="Test Reminder"))

    # Assert
    events = result.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], ReminderAddedEvent)
    assert events[0].reminder_name == "Test Reminder"
    assert events[0].day_id == day.id


@pytest.mark.asyncio
async def test_add_reminder_raises_if_day_missing():
    """Test add_reminder raises if the day doesn't exist."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day_repo = _FakeDayReadOnlyRepo(None)  # Day doesn't exist
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = _FakeUserReadOnlyRepo(user)

    ro_repos = _FakeReadOnlyRepos(day_repo, day_template_repo, user_repo)
    uow_factory = _FakeUoWFactory(day_repo, day_template_repo, user_repo)
    handler = AddReminderToDayHandler(ro_repos, uow_factory, user_id)

    # Act / Assert
    with pytest.raises(NotFoundError, match="Day"):
        await handler.handle(AddReminderToDayCommand(date=task_date, reminder="Test Reminder"))


@pytest.mark.asyncio
async def test_add_reminder_enforces_max_five():
    """Test add_reminder enforces maximum of 5 reminders."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    day.add_reminder("Reminder 1")
    day.add_reminder("Reminder 2")
    day.add_reminder("Reminder 3")
    day.add_reminder("Reminder 4")
    day.add_reminder("Reminder 5")

    day_repo = _FakeDayReadOnlyRepo(day)
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = _FakeUserReadOnlyRepo(user)

    ro_repos = _FakeReadOnlyRepos(day_repo, day_template_repo, user_repo)
    uow_factory = _FakeUoWFactory(day_repo, day_template_repo, user_repo)
    handler = AddReminderToDayHandler(ro_repos, uow_factory, user_id)

    # Act & Assert
    with pytest.raises(DomainError, match="at most 5 active reminders"):
        await handler.handle(AddReminderToDayCommand(date=task_date, reminder="Reminder 6"))
