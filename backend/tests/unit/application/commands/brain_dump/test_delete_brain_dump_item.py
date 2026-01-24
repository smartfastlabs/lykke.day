"""Unit tests for DeleteBrainDumpItemHandler."""

from datetime import date as dt_date
from uuid import uuid4

import pytest

from lykke.application.commands.brain_dump import (
    DeleteBrainDumpItemCommand,
    DeleteBrainDumpItemHandler,
)
from lykke.core.exceptions import DomainError
from lykke.domain.entities import BrainDumpEntity
from lykke.domain.events.day_events import BrainDumpItemRemovedEvent
from tests.unit.fakes import _FakeBrainDumpReadOnlyRepo, _FakeReadOnlyRepos, _FakeUoW, _FakeUoWFactory


@pytest.mark.asyncio
async def test_delete_brain_dump_item_removes_item():
    user_id = uuid4()
    item_date = dt_date(2025, 11, 27)
    item = BrainDumpEntity(
        user_id=user_id,
        date=item_date,
        text="Call mom",
    )

    brain_dump_repo = _FakeBrainDumpReadOnlyRepo(item)
    ro_repos = _FakeReadOnlyRepos(brain_dump_repo=brain_dump_repo)
    uow = _FakeUoW(brain_dump_repo=brain_dump_repo)
    uow_factory = _FakeUoWFactory(uow)
    handler = DeleteBrainDumpItemHandler(ro_repos, uow_factory, user_id)

    await handler.handle(DeleteBrainDumpItemCommand(date=item_date, item_id=item.id))

    assert len(uow.deleted) == 1
    events = uow.deleted[0].collect_events()
    assert any(isinstance(event, BrainDumpItemRemovedEvent) for event in events)


@pytest.mark.asyncio
async def test_delete_brain_dump_item_wrong_date():
    user_id = uuid4()
    item = BrainDumpEntity(
        user_id=user_id,
        date=dt_date(2025, 11, 27),
        text="Call mom",
    )

    brain_dump_repo = _FakeBrainDumpReadOnlyRepo(item)
    ro_repos = _FakeReadOnlyRepos(brain_dump_repo=brain_dump_repo)
    uow = _FakeUoW(brain_dump_repo=brain_dump_repo)
    uow_factory = _FakeUoWFactory(uow)
    handler = DeleteBrainDumpItemHandler(ro_repos, uow_factory, user_id)

    with pytest.raises(DomainError, match="not found"):
        await handler.handle(
            DeleteBrainDumpItemCommand(
                date=dt_date(2025, 11, 28),
                item_id=item.id,
            )
        )
