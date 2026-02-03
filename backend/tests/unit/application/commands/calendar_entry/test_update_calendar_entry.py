"""Unit tests for UpdateCalendarEntryHandler."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.commands.calendar_entry import (
    UpdateCalendarEntryCommand,
    UpdateCalendarEntryHandler,
)
from lykke.domain.entities import CalendarEntryEntity, UserEntity
from lykke.domain.events.calendar_entry_events import CalendarEntryUpdatedEvent
from lykke.domain.value_objects import CalendarEntryUpdateObject
from lykke.domain.value_objects.task import (
    CalendarEntryAttendanceStatus,
    TaskFrequency,
)
from tests.support.dobles import (
    create_calendar_entry_repo_double,
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
)


@pytest.mark.asyncio
async def test_update_calendar_entry_attendance_status():
    """Test updating calendar entry attendance status."""
    user_id = uuid4()
    calendar_id = uuid4()
    entry = CalendarEntryEntity(
        user_id=user_id,
        name="Test Event",
        calendar_id=calendar_id,
        platform_id="test-platform-id",
        platform="testing",
        status="confirmed",
        starts_at=datetime.now(UTC),
        frequency=TaskFrequency.ONCE,
    )

    calendar_entry_repo = create_calendar_entry_repo_double()
    allow(calendar_entry_repo).get.and_return(entry)

    ro_repos = create_read_only_repos_double(
        calendar_entry_repo=calendar_entry_repo
    )
    uow = create_uow_double(calendar_entry_repo=calendar_entry_repo)
    uow_factory = create_uow_factory_double(uow)
    handler = UpdateCalendarEntryHandler(
        ro_repos,
        uow_factory,
        UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
    )

    update_object = CalendarEntryUpdateObject(
        attendance_status=CalendarEntryAttendanceStatus.ATTENDING
    )

    await handler.handle(
        UpdateCalendarEntryCommand(
            calendar_entry_id=entry.id,
            update_data=update_object,
        )
    )

    assert len(uow.added) == 1
    updated = uow.added[0]
    assert updated.attendance_status == CalendarEntryAttendanceStatus.ATTENDING
    events = updated.collect_events()
    assert any(isinstance(event, CalendarEntryUpdatedEvent) for event in events)


@pytest.mark.asyncio
async def test_update_calendar_entry_name():
    """Test updating calendar entry name."""
    user_id = uuid4()
    calendar_id = uuid4()
    entry = CalendarEntryEntity(
        user_id=user_id,
        name="Original Name",
        calendar_id=calendar_id,
        platform_id="test-platform-id",
        platform="testing",
        status="confirmed",
        starts_at=datetime.now(UTC),
        frequency=TaskFrequency.ONCE,
    )

    calendar_entry_repo = create_calendar_entry_repo_double()
    allow(calendar_entry_repo).get.and_return(entry)

    ro_repos = create_read_only_repos_double(
        calendar_entry_repo=calendar_entry_repo
    )
    uow = create_uow_double(calendar_entry_repo=calendar_entry_repo)
    uow_factory = create_uow_factory_double(uow)
    handler = UpdateCalendarEntryHandler(
        ro_repos,
        uow_factory,
        UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
    )

    update_object = CalendarEntryUpdateObject(name="Updated Name")

    await handler.handle(
        UpdateCalendarEntryCommand(
            calendar_entry_id=entry.id,
            update_data=update_object,
        )
    )

    assert len(uow.added) == 1
    updated = uow.added[0]
    assert updated.name == "Updated Name"
    events = updated.collect_events()
    assert any(isinstance(event, CalendarEntryUpdatedEvent) for event in events)
