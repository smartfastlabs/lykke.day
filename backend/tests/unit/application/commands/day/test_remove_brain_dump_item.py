"""Unit tests for RemoveBrainDumpItemHandler."""

from datetime import date as dt_date
from uuid import uuid4

import pytest

from lykke.application.commands.day import (
    RemoveBrainDumpItemCommand,
    RemoveBrainDumpItemHandler,
)
from lykke.core.exceptions import DomainError, NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity, UserEntity
from lykke.domain.events.day_events import BrainDumpItemRemovedEvent
from tests.unit.fakes import (
    _FakeDayReadOnlyRepo,
    _FakeDayTemplateReadOnlyRepo,
    _FakeReadOnlyRepos,
    _FakeUoW,
    _FakeUoWFactory,
    _FakeUserReadOnlyRepo,
)


@pytest.mark.asyncio
async def test_remove_brain_dump_item_removes():
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    item = day.add_brain_dump_item("Test brain dump")
    day.collect_events()

    day_repo = _FakeDayReadOnlyRepo(day)
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = _FakeUserReadOnlyRepo(user)

    ro_repos = _FakeReadOnlyRepos(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow = _FakeUoW(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow_factory = _FakeUoWFactory(uow)
    handler = RemoveBrainDumpItemHandler(ro_repos, uow_factory, user_id)

    result = await handler.handle(
        RemoveBrainDumpItemCommand(date=task_date, item_id=item.id)
    )

    assert len(result.brain_dump_items) == 0
    events = result.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], BrainDumpItemRemovedEvent)


@pytest.mark.asyncio
async def test_remove_brain_dump_item_day_not_found():
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day_repo = _FakeDayReadOnlyRepo(None)
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = _FakeUserReadOnlyRepo(user)

    ro_repos = _FakeReadOnlyRepos(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow = _FakeUoW(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow_factory = _FakeUoWFactory(uow)
    handler = RemoveBrainDumpItemHandler(ro_repos, uow_factory, user_id)

    with pytest.raises(NotFoundError, match="Day"):
        await handler.handle(
            RemoveBrainDumpItemCommand(date=task_date, item_id=uuid4())
        )


@pytest.mark.asyncio
async def test_remove_brain_dump_item_raises_error():
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

    ro_repos = _FakeReadOnlyRepos(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow = _FakeUoW(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow_factory = _FakeUoWFactory(uow)
    handler = RemoveBrainDumpItemHandler(ro_repos, uow_factory, user_id)

    with pytest.raises(DomainError, match="Brain dump item"):
        await handler.handle(
            RemoveBrainDumpItemCommand(date=task_date, item_id=uuid4())
        )
