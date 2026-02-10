"""Unit tests for EnsureLykkeCalendarHandler."""

from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.commands.calendar import (
    EnsureLykkeCalendarCommand,
    EnsureLykkeCalendarHandler,
)
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntity, UserEntity
from lykke.domain.events.base import EntityCreatedEvent
from tests.support.dobles import (
    create_calendar_repo_double,
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
)


class _RepositoryFactory:
    def __init__(self, ro_repos: object) -> None:
        self._ro_repos = ro_repos

    def create(self, user: object) -> object:
        _ = user
        return self._ro_repos


@pytest.mark.asyncio
async def test_ensure_lykke_calendar_returns_existing_calendar() -> None:
    user_id = uuid4()
    platform_id = f"lykke:{user_id}"
    existing = CalendarEntity(
        user_id=user_id,
        name="Lykke Calendar",
        platform="lykke",
        platform_id=platform_id,
        auth_token_id=None,
    )

    calendar_repo = create_calendar_repo_double()
    allow(calendar_repo).search_one_or_none.with_args(
        value_objects.CalendarQuery(platform_id=platform_id)
    ).and_return(existing)
    ro_repos = create_read_only_repos_double(calendar_repo=calendar_repo)

    uow = create_uow_double(calendar_repo=calendar_repo)
    handler = EnsureLykkeCalendarHandler(
        user=UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
        uow_factory=create_uow_factory_double(uow),
        repository_factory=_RepositoryFactory(ro_repos),
    )

    result = await handler.handle(EnsureLykkeCalendarCommand())

    assert result is existing
    assert uow.added == []


@pytest.mark.asyncio
async def test_ensure_lykke_calendar_creates_calendar_when_missing() -> None:
    user_id = uuid4()
    platform_id = f"lykke:{user_id}"

    calendar_repo = create_calendar_repo_double()
    allow(calendar_repo).search_one_or_none.with_args(
        value_objects.CalendarQuery(platform_id=platform_id)
    ).and_return(None)
    ro_repos = create_read_only_repos_double(calendar_repo=calendar_repo)

    uow = create_uow_double(calendar_repo=calendar_repo)
    handler = EnsureLykkeCalendarHandler(
        user=UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
        uow_factory=create_uow_factory_double(uow),
        repository_factory=_RepositoryFactory(ro_repos),
    )

    created = await handler.handle(EnsureLykkeCalendarCommand())

    assert created.user_id == user_id
    assert created.platform == "lykke"
    assert created.platform_id == platform_id
    assert created.name == "Lykke Calendar"
    assert created.auth_token_id is None
    assert uow.added == [created]

    events = created.collect_events()
    assert any(isinstance(e, EntityCreatedEvent) for e in events)

