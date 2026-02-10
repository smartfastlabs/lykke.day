"""Unit tests for DeleteCalendarEntryHandler."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.commands.calendar_entry import (
    DeleteCalendarEntryCommand,
    DeleteCalendarEntryHandler,
)
from lykke.domain.entities import CalendarEntryEntity, UserEntity
from lykke.domain.events.base import EntityDeletedEvent
from lykke.domain.value_objects.task import TaskFrequency
from tests.support.dobles import (
    create_calendar_entry_repo_double,
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
async def test_delete_calendar_entry_marks_entry_deleted() -> None:
    user_id = uuid4()
    entry = CalendarEntryEntity(
        user_id=user_id,
        name="Event",
        calendar_id=uuid4(),
        platform_id="event-1",
        platform="google",
        status="confirmed",
        starts_at=datetime(2026, 2, 9, 9, 0, tzinfo=UTC),
        frequency=TaskFrequency.ONCE,
    )

    calendar_entry_repo = create_calendar_entry_repo_double()
    allow(calendar_entry_repo).get.with_args(entry.id).and_return(entry)
    ro_repos = create_read_only_repos_double(calendar_entry_repo=calendar_entry_repo)

    uow = create_uow_double(calendar_entry_repo=calendar_entry_repo)
    handler = DeleteCalendarEntryHandler(
        user=UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
        uow_factory=create_uow_factory_double(uow),
        repository_factory=_RepositoryFactory(ro_repos),
    )

    await handler.handle(DeleteCalendarEntryCommand(calendar_entry_id=entry.id))

    assert uow.deleted == [entry]
    events = entry.collect_events()
    assert any(isinstance(e, EntityDeletedEvent) for e in events)

