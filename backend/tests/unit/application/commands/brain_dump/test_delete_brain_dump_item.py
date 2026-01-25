"""Unit tests for DeleteBrainDumpHandler."""

from datetime import date as dt_date
from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.commands.brain_dump import (
    DeleteBrainDumpCommand,
    DeleteBrainDumpHandler,
)
from lykke.core.exceptions import DomainError
from lykke.domain.entities import BrainDumpEntity
from lykke.domain.events.day_events import BrainDumpItemRemovedEvent
from tests.support.dobles import (
    create_brain_dump_repo_double,
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
)


@pytest.mark.asyncio
async def test_delete_brain_dump_removes_item():
    user_id = uuid4()
    item_date = dt_date(2025, 11, 27)
    item = BrainDumpEntity(
        user_id=user_id,
        date=item_date,
        text="Call mom",
    )

    brain_dump_repo = create_brain_dump_repo_double()
    allow(brain_dump_repo).get.and_return(item)

    ro_repos = create_read_only_repos_double(brain_dump_repo=brain_dump_repo)
    uow = create_uow_double(brain_dump_repo=brain_dump_repo)
    uow_factory = create_uow_factory_double(uow)
    handler = DeleteBrainDumpHandler(ro_repos, uow_factory, user_id)

    await handler.handle(DeleteBrainDumpCommand(date=item_date, item_id=item.id))

    assert len(uow.deleted) == 1
    events = uow.deleted[0].collect_events()
    assert any(isinstance(event, BrainDumpItemRemovedEvent) for event in events)


@pytest.mark.asyncio
async def test_delete_brain_dump_wrong_date():
    user_id = uuid4()
    item = BrainDumpEntity(
        user_id=user_id,
        date=dt_date(2025, 11, 27),
        text="Call mom",
    )

    brain_dump_repo = create_brain_dump_repo_double()
    allow(brain_dump_repo).get.and_return(item)

    ro_repos = create_read_only_repos_double(brain_dump_repo=brain_dump_repo)
    uow = create_uow_double(brain_dump_repo=brain_dump_repo)
    uow_factory = create_uow_factory_double(uow)
    handler = DeleteBrainDumpHandler(ro_repos, uow_factory, user_id)

    with pytest.raises(DomainError, match="not found"):
        await handler.handle(
            DeleteBrainDumpCommand(
                date=dt_date(2025, 11, 28),
                item_id=item.id,
            )
        )
