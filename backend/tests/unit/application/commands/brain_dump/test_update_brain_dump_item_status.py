"""Unit tests for UpdateBrainDumpItemStatusHandler."""

from datetime import date as dt_date
from uuid import uuid4

import pytest

from lykke.application.commands.brain_dump import (
    UpdateBrainDumpItemStatusCommand,
    UpdateBrainDumpItemStatusHandler,
)
from lykke.core.exceptions import DomainError
from lykke.domain import value_objects
from lykke.domain.entities import BrainDumpEntity
from lykke.domain.events.day_events import BrainDumpItemStatusChangedEvent
from tests.unit.fakes import _FakeBrainDumpReadOnlyRepo, _FakeReadOnlyRepos, _FakeUoW, _FakeUoWFactory


@pytest.mark.asyncio
async def test_update_brain_dump_item_status_updates_item():
    user_id = uuid4()
    item_date = dt_date(2025, 11, 27)
    item = BrainDumpEntity(
        user_id=user_id,
        date=item_date,
        text="Finish task",
    )

    brain_dump_repo = _FakeBrainDumpReadOnlyRepo(item)
    ro_repos = _FakeReadOnlyRepos(brain_dump_repo=brain_dump_repo)
    uow = _FakeUoW(brain_dump_repo=brain_dump_repo)
    uow_factory = _FakeUoWFactory(uow)
    handler = UpdateBrainDumpItemStatusHandler(ro_repos, uow_factory, user_id)

    await handler.handle(
        UpdateBrainDumpItemStatusCommand(
            date=item_date,
            item_id=item.id,
            status=value_objects.BrainDumpItemStatus.COMPLETE,
        )
    )

    assert len(uow.added) == 1
    updated = uow.added[0]
    assert updated.status == value_objects.BrainDumpItemStatus.COMPLETE
    events = updated.collect_events()
    assert any(isinstance(event, BrainDumpItemStatusChangedEvent) for event in events)


@pytest.mark.asyncio
async def test_update_brain_dump_item_status_wrong_date():
    user_id = uuid4()
    item = BrainDumpEntity(
        user_id=user_id,
        date=dt_date(2025, 11, 27),
        text="Finish task",
    )

    brain_dump_repo = _FakeBrainDumpReadOnlyRepo(item)
    ro_repos = _FakeReadOnlyRepos(brain_dump_repo=brain_dump_repo)
    uow = _FakeUoW(brain_dump_repo=brain_dump_repo)
    uow_factory = _FakeUoWFactory(uow)
    handler = UpdateBrainDumpItemStatusHandler(ro_repos, uow_factory, user_id)

    with pytest.raises(DomainError, match="not found"):
        await handler.handle(
            UpdateBrainDumpItemStatusCommand(
                date=dt_date(2025, 11, 28),
                item_id=item.id,
                status=value_objects.BrainDumpItemStatus.PUNT,
            )
        )
