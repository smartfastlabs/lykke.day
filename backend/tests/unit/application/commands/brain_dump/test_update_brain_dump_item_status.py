"""Unit tests for UpdateBrainDumpStatusHandler."""

from datetime import date as dt_date
from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.commands.brain_dump import (
    UpdateBrainDumpStatusCommand,
    UpdateBrainDumpStatusHandler,
)
from lykke.core.exceptions import DomainError
from lykke.domain import value_objects
from lykke.domain.entities import BrainDumpEntity
from lykke.domain.events.day_events import BrainDumpItemStatusChangedEvent
from tests.support.dobles import (
    create_brain_dump_repo_double,
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
)


@pytest.mark.asyncio
async def test_update_brain_dump_status_updates_item():
    user_id = uuid4()
    item_date = dt_date(2025, 11, 27)
    item = BrainDumpEntity(
        user_id=user_id,
        date=item_date,
        text="Finish task",
    )

    brain_dump_repo = create_brain_dump_repo_double()
    allow(brain_dump_repo).get.and_return(item)

    ro_repos = create_read_only_repos_double(brain_dump_repo=brain_dump_repo)
    uow = create_uow_double(brain_dump_repo=brain_dump_repo)
    uow_factory = create_uow_factory_double(uow)
    handler = UpdateBrainDumpStatusHandler(ro_repos, uow_factory, user_id)

    await handler.handle(
        UpdateBrainDumpStatusCommand(
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
async def test_update_brain_dump_status_wrong_date():
    user_id = uuid4()
    item = BrainDumpEntity(
        user_id=user_id,
        date=dt_date(2025, 11, 27),
        text="Finish task",
    )

    brain_dump_repo = create_brain_dump_repo_double()
    allow(brain_dump_repo).get.and_return(item)

    ro_repos = create_read_only_repos_double(brain_dump_repo=brain_dump_repo)
    uow = create_uow_double(brain_dump_repo=brain_dump_repo)
    uow_factory = create_uow_factory_double(uow)
    handler = UpdateBrainDumpStatusHandler(ro_repos, uow_factory, user_id)

    with pytest.raises(DomainError, match="not found"):
        await handler.handle(
            UpdateBrainDumpStatusCommand(
                date=dt_date(2025, 11, 28),
                item_id=item.id,
                status=value_objects.BrainDumpItemStatus.PUNT,
            )
        )
