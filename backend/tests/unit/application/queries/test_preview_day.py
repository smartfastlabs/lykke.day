"""Unit tests for PreviewDayHandler."""

from datetime import date as dt_date
from uuid import uuid4

import pytest

from lykke.application.queries.preview_day import PreviewDayHandler, PreviewDayQuery
from lykke.application.queries.preview_tasks import PreviewTasksHandler
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity, UserEntity
from tests.unit.fakes import (
    _FakeCalendarEntryReadOnlyRepo,
    _FakeDayReadOnlyRepo,
    _FakeDayTemplateReadOnlyRepo,
    _FakeReadOnlyRepos,
    _FakeRoutineReadOnlyRepo,
    _FakeTaskDefinitionReadOnlyRepo,
    _FakeUserReadOnlyRepo,
)


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
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
        calendar_entry_repo=calendar_entry_repo,
        routine_repo=_FakeRoutineReadOnlyRepo(),
        task_definition_repo=_FakeTaskDefinitionReadOnlyRepo(),
    )
    handler = PreviewDayHandler(ro_repos, user_id)

    # Act
    result = await handler.handle(
        PreviewDayQuery(date=task_date, template_id=template.id)
    )

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
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
        calendar_entry_repo=calendar_entry_repo,
        routine_repo=_FakeRoutineReadOnlyRepo(),
        task_definition_repo=_FakeTaskDefinitionReadOnlyRepo(),
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
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
        calendar_entry_repo=calendar_entry_repo,
        routine_repo=_FakeRoutineReadOnlyRepo(),
        task_definition_repo=_FakeTaskDefinitionReadOnlyRepo(),
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
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
        calendar_entry_repo=calendar_entry_repo,
        routine_repo=_FakeRoutineReadOnlyRepo(),
        task_definition_repo=_FakeTaskDefinitionReadOnlyRepo(),
    )
    handler = PreviewDayHandler(ro_repos, user_id)

    # Act
    result = await handler.handle(
        PreviewDayQuery(date=task_date, template_id=template.id)
    )

    # Assert
    assert result.calendar_entries == mock_entries
