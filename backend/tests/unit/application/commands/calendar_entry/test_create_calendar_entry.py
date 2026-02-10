"""Unit tests for CreateCalendarEntryHandler."""

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

import pytest

from lykke.application.commands.calendar import EnsureLykkeCalendarHandler
from lykke.application.commands.calendar import EnsureLykkeCalendarCommand
from lykke.application.commands.calendar_entry import (
    CreateCalendarEntryCommand,
    CreateCalendarEntryHandler,
)
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntity, CalendarEntryEntity, UserEntity
from lykke.domain.events.base import EntityCreatedEvent
from tests.support.dobles import (
    create_calendar_entry_repo_double,
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
)


@dataclass
class _EnsureCalendarHandlerStub:
    calendar: CalendarEntity

    async def handle(self, command: EnsureLykkeCalendarCommand) -> CalendarEntity:
        _ = command
        return self.calendar


@dataclass
class _CommandFactory:
    handlers: dict[type[object], object]
    query_factory: object | None = None

    def can_create(self, handler_class: type[object]) -> bool:
        return handler_class in self.handlers

    def create(self, handler_class: type[object]) -> object:
        return self.handlers[handler_class]


class _RepositoryFactory:
    def __init__(self, ro_repos: object) -> None:
        self._ro_repos = ro_repos

    def create(self, user: object) -> object:
        _ = user
        return self._ro_repos


@pytest.mark.asyncio
async def test_create_calendar_entry_creates_lykke_entry_with_utc_times() -> None:
    user_id = uuid4()
    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="!",
        settings=value_objects.UserSetting(timezone="America/Los_Angeles"),
    )

    calendar = CalendarEntity(
        user_id=user_id,
        name="Lykke Calendar",
        platform="lykke",
        platform_id=f"lykke:{user_id}",
        auth_token_id=None,
    )

    command_factory = _CommandFactory(
        handlers={
            EnsureLykkeCalendarHandler: _EnsureCalendarHandlerStub(calendar=calendar),
        }
    )

    calendar_entry_repo = create_calendar_entry_repo_double()
    ro_repos = create_read_only_repos_double(calendar_entry_repo=calendar_entry_repo)
    uow = create_uow_double(calendar_entry_repo=calendar_entry_repo)

    handler = CreateCalendarEntryHandler(
        user=user,
        command_factory=command_factory,
        uow_factory=create_uow_factory_double(uow),
        repository_factory=_RepositoryFactory(ro_repos),
    )

    starts_at = datetime(2026, 2, 9, 9, 0)  # naive
    ends_at = datetime(2026, 2, 9, 10, 0)  # naive
    result = await handler.handle(
        CreateCalendarEntryCommand(
            name="Deep work",
            starts_at=starts_at,
            ends_at=ends_at,
            category=None,
        )
    )

    assert isinstance(result, CalendarEntryEntity)
    assert uow.added == [result]

    assert result.user_id == user_id
    assert result.calendar_id == calendar.id
    assert result.platform == "lykke"
    assert result.status == "confirmed"
    assert result.frequency == value_objects.TaskFrequency.ONCE
    assert result.user_timezone == "America/Los_Angeles"
    assert isinstance(result.platform_id, str)
    assert len(result.platform_id) == 32  # uuid4 hex

    assert result.starts_at.tzinfo is not None
    assert result.ends_at is not None and result.ends_at.tzinfo is not None

    events = result.collect_events()
    assert any(isinstance(e, EntityCreatedEvent) for e in events)

