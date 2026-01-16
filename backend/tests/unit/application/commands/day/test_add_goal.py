"""Unit tests for AddGoalToDayHandler."""

import datetime
from datetime import UTC, date as dt_date
from uuid import uuid4

import pytest

from lykke.application.commands.day import AddGoalToDayHandler
from lykke.core.exceptions import DomainError, NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity, UserEntity
from lykke.domain.events.day_events import GoalAddedEvent


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
        self.push_subscription_ro_repo = fake
        self.routine_ro_repo = fake
        self.task_definition_ro_repo = fake
        self.task_ro_repo = fake
        self.time_block_definition_ro_repo = fake
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

    async def create(self, entity):
        self.created.append(entity)
        entity.create()


class _FakeUoWFactory:
    def __init__(self, day_repo, day_template_repo, user_repo) -> None:
        self.uow = _FakeUoW(day_repo, day_template_repo, user_repo)

    def create(self, _user_id):
        return self.uow


@pytest.mark.asyncio
async def test_add_goal_adds_goal_to_existing_day():
    """Test add_goal adds a goal to an existing day."""
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
    handler = AddGoalToDayHandler(ro_repos, uow_factory, user_id)

    # Act
    result = await handler.add_goal(date=task_date, name="Test Goal")

    # Assert
    assert len(result.goals) == 1
    assert result.goals[0].name == "Test Goal"
    assert result.goals[0].status == value_objects.GoalStatus.INCOMPLETE
    assert len(uow_factory.uow.added) == 1
    assert uow_factory.uow.added[0] == result


@pytest.mark.asyncio
async def test_add_goal_emits_domain_event():
    """Test add_goal emits GoalAddedEvent."""
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
    handler = AddGoalToDayHandler(ro_repos, uow_factory, user_id)

    # Act
    result = await handler.add_goal(date=task_date, name="Test Goal")

    # Assert
    events = result.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], GoalAddedEvent)
    assert events[0].goal_name == "Test Goal"
    assert events[0].day_id == day.id


@pytest.mark.asyncio
async def test_add_goal_creates_day_if_not_exists():
    """Test add_goal creates a day if it doesn't exist."""
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
    handler = AddGoalToDayHandler(ro_repos, uow_factory, user_id)

    # Act
    result = await handler.add_goal(date=task_date, name="Test Goal")

    # Assert
    assert len(uow_factory.uow.created) == 1
    created_day = uow_factory.uow.created[0]
    assert isinstance(created_day, DayEntity)
    assert created_day.date == task_date
    assert len(result.goals) == 1
    assert result.goals[0].name == "Test Goal"


@pytest.mark.asyncio
async def test_add_goal_enforces_max_three():
    """Test add_goal enforces maximum of 3 goals."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    day.add_goal("Goal 1")
    day.add_goal("Goal 2")
    day.add_goal("Goal 3")

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
    handler = AddGoalToDayHandler(ro_repos, uow_factory, user_id)

    # Act & Assert
    with pytest.raises(DomainError, match="at most 3 goals"):
        await handler.add_goal(date=task_date, name="Goal 4")
