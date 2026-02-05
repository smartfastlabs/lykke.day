"""Unit tests for PreviewDayHandler."""

from datetime import date as dt_date
from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.queries.preview_day import PreviewDayHandler, PreviewDayQuery
from lykke.application.queries.preview_tasks import PreviewTasksHandler
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity, UserEntity
from tests.support.dobles import (
    create_calendar_entry_repo_double,
    create_day_repo_double,
    create_day_template_repo_double,
    create_read_only_repos_double,
    create_routine_definition_repo_double,
    create_task_definition_repo_double,
)


class _RepositoryFactory:
    def __init__(self, ro_repos: object) -> None:
        self._ro_repos = ro_repos

    def create(self, user: object) -> object:
        _ = user
        return self._ro_repos


@pytest.mark.asyncio
async def test_preview_day_uses_provided_template():
    """Verify preview_day uses provided template_id."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_definition_ids=[],
        time_blocks=[],
    )

    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )

    # Setup repositories
    day_repo = create_day_repo_double()
    day_id = DayEntity.id_from_date_and_user(task_date, user_id)
    allow(day_repo).get.with_args(day_id).and_raise(NotFoundError("Day not found"))

    day_template_repo = create_day_template_repo_double()
    allow(day_template_repo).get.with_args(template.id).and_return(template)
    allow(day_template_repo).search_one.and_return(template)

    calendar_entry_repo = create_calendar_entry_repo_double()
    allow(calendar_entry_repo).search.and_return([])

    routine_definition_repo = create_routine_definition_repo_double()
    allow(routine_definition_repo).all.and_return([])

    task_definition_repo = create_task_definition_repo_double()
    allow(task_definition_repo).search.and_return([])

    ro_repos = create_read_only_repos_double(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        calendar_entry_repo=calendar_entry_repo,
        routine_definition_repo=routine_definition_repo,
        task_definition_repo=task_definition_repo,
    )
    handler = PreviewDayHandler(
        user=user,
        repository_factory=_RepositoryFactory(ro_repos),
    )
    handler.preview_tasks_handler = PreviewTasksHandler(
        user=user,
        repository_factory=_RepositoryFactory(ro_repos),
    )

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
        routine_definition_ids=[],
        time_blocks=[],
    )

    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )

    # Setup repositories - no existing day
    day_repo = create_day_repo_double()
    day_id = DayEntity.id_from_date_and_user(task_date, user_id)
    allow(day_repo).get.with_args(day_id).and_raise(NotFoundError("Day not found"))

    day_template_repo = create_day_template_repo_double()
    allow(day_template_repo).get.and_return(template)
    allow(day_template_repo).search_one.and_return(template)

    calendar_entry_repo = create_calendar_entry_repo_double()
    allow(calendar_entry_repo).search.and_return([])

    routine_definition_repo = create_routine_definition_repo_double()
    allow(routine_definition_repo).all.and_return([])

    task_definition_repo = create_task_definition_repo_double()
    allow(task_definition_repo).search.and_return([])

    ro_repos = create_read_only_repos_double(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        calendar_entry_repo=calendar_entry_repo,
        routine_definition_repo=routine_definition_repo,
        task_definition_repo=task_definition_repo,
    )
    handler = PreviewDayHandler(
        user=user,
        repository_factory=_RepositoryFactory(ro_repos),
    )
    handler.preview_tasks_handler = PreviewTasksHandler(
        user=user,
        repository_factory=_RepositoryFactory(ro_repos),
    )

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
        routine_definition_ids=[],
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
    day_repo = create_day_repo_double()
    day_id = DayEntity.id_from_date_and_user(task_date, user_id)
    allow(day_repo).get.with_args(day_id).and_return(existing_day)

    day_template_repo = create_day_template_repo_double()
    allow(day_template_repo).get.and_return(template)
    allow(day_template_repo).search_one.and_return(template)

    calendar_entry_repo = create_calendar_entry_repo_double()
    allow(calendar_entry_repo).search.and_return([])

    routine_definition_repo = create_routine_definition_repo_double()
    allow(routine_definition_repo).all.and_return([])

    task_definition_repo = create_task_definition_repo_double()
    allow(task_definition_repo).search.and_return([])

    ro_repos = create_read_only_repos_double(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        calendar_entry_repo=calendar_entry_repo,
        routine_definition_repo=routine_definition_repo,
        task_definition_repo=task_definition_repo,
    )
    handler = PreviewDayHandler(
        user=user,
        repository_factory=_RepositoryFactory(ro_repos),
    )
    handler.preview_tasks_handler = PreviewTasksHandler(
        user=user,
        repository_factory=_RepositoryFactory(ro_repos),
    )

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
        routine_definition_ids=[],
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
    day_repo = create_day_repo_double()
    day_id = DayEntity.id_from_date_and_user(task_date, user_id)
    allow(day_repo).get.with_args(day_id).and_raise(NotFoundError("Day not found"))

    day_template_repo = create_day_template_repo_double()
    allow(day_template_repo).get.and_return(template)
    allow(day_template_repo).search_one.and_return(template)

    calendar_entry_repo = create_calendar_entry_repo_double()
    allow(calendar_entry_repo).search.and_return(mock_entries)

    routine_definition_repo = create_routine_definition_repo_double()
    allow(routine_definition_repo).all.and_return([])

    task_definition_repo = create_task_definition_repo_double()
    allow(task_definition_repo).search.and_return([])

    ro_repos = create_read_only_repos_double(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        calendar_entry_repo=calendar_entry_repo,
        routine_definition_repo=routine_definition_repo,
        task_definition_repo=task_definition_repo,
    )
    handler = PreviewDayHandler(
        user=user,
        repository_factory=_RepositoryFactory(ro_repos),
    )
    handler.preview_tasks_handler = PreviewTasksHandler(
        user=user,
        repository_factory=_RepositoryFactory(ro_repos),
    )

    # Act
    result = await handler.handle(
        PreviewDayQuery(date=task_date, template_id=template.id)
    )

    # Assert
    assert result.calendar_entries == mock_entries
