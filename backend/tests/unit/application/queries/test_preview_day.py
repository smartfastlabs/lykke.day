"""Unit tests for PreviewDayHandler."""

from datetime import date as dt_date
from uuid import uuid4

import pytest

from lykke.application.queries.preview_day import PreviewDayHandler, PreviewDayQuery
from lykke.application.queries.preview_tasks import PreviewTasksHandler
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity, UserEntity


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

    async def get(self, template_id):
        if template_id == self._template.id:
            return self._template
        raise NotFoundError(f"Template {template_id} not found")

    async def search_one(self, query):
        return self._template


class _FakeUserReadOnlyRepo:
    """Fake user repository for testing."""

    def __init__(self, user: UserEntity) -> None:
        self._user = user

    async def get(self, user_id):
        if user_id == self._user.id:
            return self._user
        raise NotFoundError(f"User {user_id} not found")


class _FakeCalendarEntryReadOnlyRepo:
    """Fake calendar entry repository for testing."""

    def __init__(self, entries=None) -> None:
        self._entries = entries or []

    async def search(self, query):
        return self._entries


class _FakeRoutineReadOnlyRepo:
    """Fake routine repository for testing."""

    async def all(self):
        return []


class _FakeTaskDefinitionReadOnlyRepo:
    """Fake task definition repository for testing."""

    async def search(self, query):
        return []


class _FakeReadOnlyRepos:
    """Lightweight container matching ReadOnlyRepositories protocol."""

    def __init__(
        self,
        day_repo: _FakeDayReadOnlyRepo,
        day_template_repo: _FakeDayTemplateReadOnlyRepo,
        user_repo: _FakeUserReadOnlyRepo,
        calendar_entry_repo: _FakeCalendarEntryReadOnlyRepo,
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
        self.notification_ro_repo = fake
        self.push_notification_ro_repo = fake
        self.push_subscription_ro_repo = fake
        self.routine_ro_repo = _FakeRoutineReadOnlyRepo()
        self.task_definition_ro_repo = _FakeTaskDefinitionReadOnlyRepo()
        self.task_ro_repo = fake
        self.template_ro_repo = fake
        self.time_block_definition_ro_repo = fake
        self.usecase_config_ro_repo = fake
        self.user_ro_repo = user_repo


@pytest.mark.asyncio
async def test_preview_day_uses_provided_template():
    """Verify preview_day uses provided template_id."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )

    # Setup repositories
    day_repo = _FakeDayReadOnlyRepo(None)
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    user_repo = _FakeUserReadOnlyRepo(user)
    calendar_entry_repo = _FakeCalendarEntryReadOnlyRepo([])

    ro_repos = _FakeReadOnlyRepos(
        day_repo, day_template_repo, user_repo, calendar_entry_repo
    )
    handler = PreviewDayHandler(ro_repos, user_id)

    # Act
    result = await handler.handle(PreviewDayQuery(date=task_date, template_id=template.id))

    # Assert
    assert result.day.date == task_date
    assert result.day.user_id == user_id
    assert result.day.template == template
    assert isinstance(result.tasks, list)
    assert isinstance(result.calendar_entries, list)


@pytest.mark.asyncio
async def test_preview_day_falls_back_to_user_default_template():
    """Verify preview_day uses user's default template when none provided."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)  # Wednesday (weekday=2)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )

    # Setup repositories - no existing day
    day_repo = _FakeDayReadOnlyRepo(None)
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    user_repo = _FakeUserReadOnlyRepo(user)
    calendar_entry_repo = _FakeCalendarEntryReadOnlyRepo([])

    ro_repos = _FakeReadOnlyRepos(
        day_repo, day_template_repo, user_repo, calendar_entry_repo
    )
    handler = PreviewDayHandler(ro_repos, user_id)

    # Act - no template_id provided
    result = await handler.handle(PreviewDayQuery(date=task_date))

    # Assert
    assert result.day.template == template


@pytest.mark.asyncio
async def test_preview_day_uses_existing_day_template_if_available():
    """Verify preview_day uses template from existing day if available."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="custom",
        routine_ids=[],
        time_blocks=[],
    )

    existing_day = DayEntity.create_for_date(task_date, user_id, template)

    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )

    # Setup repositories with existing day
    day_repo = _FakeDayReadOnlyRepo(existing_day)
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    user_repo = _FakeUserReadOnlyRepo(user)
    calendar_entry_repo = _FakeCalendarEntryReadOnlyRepo([])

    ro_repos = _FakeReadOnlyRepos(
        day_repo, day_template_repo, user_repo, calendar_entry_repo
    )
    handler = PreviewDayHandler(ro_repos, user_id)

    # Act - no template_id provided
    result = await handler.handle(PreviewDayQuery(date=task_date))

    # Assert - should use template from existing day
    assert result.day.template == template
    assert result.day.template.slug == "custom"


@pytest.mark.asyncio
async def test_preview_day_returns_calendar_entries():
    """Verify preview_day includes calendar entries for the date."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )

    # Create mock calendar entries
    mock_entries = [{"name": "Meeting 1"}, {"name": "Meeting 2"}]

    # Setup repositories
    day_repo = _FakeDayReadOnlyRepo(None)
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    user_repo = _FakeUserReadOnlyRepo(user)
    calendar_entry_repo = _FakeCalendarEntryReadOnlyRepo(mock_entries)

    ro_repos = _FakeReadOnlyRepos(
        day_repo, day_template_repo, user_repo, calendar_entry_repo
    )
    handler = PreviewDayHandler(ro_repos, user_id)

    # Act
    result = await handler.handle(PreviewDayQuery(date=task_date, template_id=template.id))

    # Assert
    assert result.calendar_entries == mock_entries
