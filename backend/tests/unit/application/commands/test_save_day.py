"""Unit tests for SaveDayHandler."""

from datetime import date as dt_date
from uuid import uuid4

import pytest

from lykke.application.commands.day import SaveDayHandler
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity


class _FakeReadOnlyRepos:
    """Lightweight container matching ReadOnlyRepositories protocol."""

    def __init__(self) -> None:
        fake = object()
        self.auth_token_ro_repo = fake
        self.calendar_entry_ro_repo = fake
        self.calendar_entry_series_ro_repo = fake
        self.calendar_ro_repo = fake
        self.day_ro_repo = fake
        self.day_template_ro_repo = fake
        self.push_subscription_ro_repo = fake
        self.routine_ro_repo = fake
        self.task_definition_ro_repo = fake
        self.task_ro_repo = fake
        self.time_block_definition_ro_repo = fake
        self.user_ro_repo = fake


class _FakeUoW:
    """Minimal UnitOfWork that just collects added entities."""

    def __init__(self) -> None:
        self.added = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    def add(self, entity):
        self.added.append(entity)


class _FakeUoWFactory:
    def __init__(self) -> None:
        self.uow = _FakeUoW()

    def create(self, _user_id):
        return self.uow


@pytest.mark.asyncio
async def test_save_day_adds_day_to_uow():
    """Verify day is added to UoW when saving."""
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

    # Setup handler
    ro_repos = _FakeReadOnlyRepos()
    uow_factory = _FakeUoWFactory()
    handler = SaveDayHandler(ro_repos, uow_factory, user_id)

    # Act
    result = await handler.save_day(day)

    # Assert
    assert result == day
    assert len(uow_factory.uow.added) == 1
    assert uow_factory.uow.added[0] == day


@pytest.mark.asyncio
async def test_save_day_preserves_day_properties():
    """Verify day properties are preserved when saving."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    day.status = value_objects.DayStatus.SCHEDULED
    day.tags = [value_objects.DayTag.WORKDAY]

    ro_repos = _FakeReadOnlyRepos()
    uow_factory = _FakeUoWFactory()
    handler = SaveDayHandler(ro_repos, uow_factory, user_id)

    # Act
    result = await handler.save_day(day)

    # Assert
    assert result.status == value_objects.DayStatus.SCHEDULED
    assert result.tags == [value_objects.DayTag.WORKDAY]
    assert result.date == task_date
    assert result.user_id == user_id
    assert result.template == template


@pytest.mark.asyncio
async def test_save_day_returns_same_day_instance():
    """Verify save_day returns the same day instance."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)

    ro_repos = _FakeReadOnlyRepos()
    uow_factory = _FakeUoWFactory()
    handler = SaveDayHandler(ro_repos, uow_factory, user_id)

    # Act
    result = await handler.save_day(day)

    # Assert - should be the exact same instance
    assert result is day
