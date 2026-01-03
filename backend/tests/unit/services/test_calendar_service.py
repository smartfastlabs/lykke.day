"""Unit tests for CalendarService."""

import datetime
from datetime import UTC, timedelta
from uuid import UUID, uuid4

import pytest
from dobles import allow
from planned.application.services import CalendarService
from planned.core.exceptions import NotFoundError, TokenExpiredError
from planned.domain.entities import Calendar, CalendarEntry
from planned.infrastructure import data_objects
from planned.domain.value_objects.task import TaskFrequency




@pytest.mark.asyncio
async def test_sync(
    test_user,
    mock_auth_token_repo,
    mock_calendar_repo,
    mock_calendar_entry_repo,
    mock_google_gateway,
    mock_uow_factory,
    test_datetime_noon,
):
    """Test syncing a calendar."""
    calendar = Calendar(
        user_id=UUID(str(uuid4())),
        name="Test Calendar",
        auth_token_id=uuid4(),
        platform="google",
        platform_id="platform-id",
    )

    token = data_objects.AuthToken(
        id=calendar.auth_token_id,
        user_id=calendar.user_id,
        platform="google",
        token="token",
    )

    calendar_entry = CalendarEntry(
        user_id=calendar.user_id,
        name="Calendar Entry",
        frequency=TaskFrequency.ONCE,
        calendar_id=calendar.id,
        platform_id="entry-id",
        platform="google",
        status="confirmed",
        starts_at=test_datetime_noon,
    )

    # Mock UOW methods
    uow = mock_uow_factory.create(test_user.id)
    allow(mock_calendar_repo).get(calendar.id).and_return(calendar)
    allow(mock_auth_token_repo).get(token.id).and_return(token)
    allow(mock_google_gateway).load_calendar_events.and_return([calendar_entry])
    allow(mock_calendar_entry_repo).put.and_return(calendar_entry)

    service = CalendarService(
        user=test_user,
        uow_factory=mock_uow_factory,
        google_gateway=mock_google_gateway,
    )

    calendar_entries, deleted_calendar_entries = await service.sync(calendar)

    assert len(calendar_entries) == 1
    assert calendar.last_sync_at is not None


@pytest.mark.asyncio
async def test_sync_all(
    test_user,
    mock_auth_token_repo, mock_calendar_repo, mock_calendar_entry_repo, mock_google_gateway, mock_uow_factory
):
    """Test syncing all calendars."""
    calendar1 = Calendar(
        user_id=UUID(str(uuid4())),
        name="Calendar 1",
        auth_token_id=uuid4(),
        platform="google",
        platform_id="platform-id-1",
    )
    calendar2 = Calendar(
        user_id=UUID(str(uuid4())),
        name="Calendar 2",
        auth_token_id=uuid4(),
        platform="google",
        platform_id="platform-id-2",
    )

    allow(mock_calendar_repo).all().and_return([calendar1, calendar2])
    allow(mock_auth_token_repo).get.and_raise(
        TokenExpiredError("Token expired")
    )
    allow(mock_calendar_entry_repo).put.and_return(None)

    service = CalendarService(
        user=test_user,
        uow_factory=mock_uow_factory,
        google_gateway=mock_google_gateway,
    )

    # Should handle errors gracefully
    await service.sync_all()


@pytest.mark.asyncio
async def test_sync_with_last_sync_at(
    test_user,
    mock_auth_token_repo,
    mock_calendar_repo,
    mock_calendar_entry_repo,
    mock_google_gateway,
    mock_uow_factory,
    test_datetime_noon,
):
    """Test syncing a calendar with last_sync_at set uses it for lookback."""
    calendar = Calendar(
        user_id=UUID(str(uuid4())),
        name="Test Calendar",
        auth_token_id=uuid4(),
        platform="google",
        platform_id="platform-id",
        last_sync_at=test_datetime_noon - timedelta(hours=1),
    )

    token = data_objects.AuthToken(
        id=calendar.auth_token_id,
        user_id=calendar.user_id,
        platform="google",
        token="token",
    )

    calendar_entry = CalendarEntry(
        user_id=calendar.user_id,
        name="Calendar Entry",
        frequency=TaskFrequency.ONCE,
        calendar_id=calendar.id,
        platform_id="entry-id",
        platform="google",
        status="confirmed",
        starts_at=test_datetime_noon,
    )

    expected_lookback = calendar.last_sync_at - timedelta(minutes=30)

    # Mock UOW methods
    allow(mock_calendar_repo).get(calendar.id).and_return(calendar)
    allow(mock_auth_token_repo).get(token.id).and_return(token)
    allow(mock_google_gateway).load_calendar_events(
        calendar,
        lookback=expected_lookback,
        token=token,
    ).and_return([calendar_entry])
    allow(mock_calendar_entry_repo).put.and_return(calendar_entry)

    service = CalendarService(
        user=test_user,
        uow_factory=mock_uow_factory,
        google_gateway=mock_google_gateway,
    )

    calendar_entries, deleted_calendar_entries = await service.sync(calendar)

    assert len(calendar_entries) == 1
    assert calendar.last_sync_at is not None
    assert calendar.last_sync_at > expected_lookback


@pytest.mark.asyncio
async def test_sync_unsupported_platform(
    test_user,
    mock_auth_token_repo, mock_calendar_repo, mock_calendar_entry_repo, mock_google_gateway, mock_uow_factory
):
    """Test syncing a calendar with unsupported platform raises NotImplementedError."""
    calendar = Calendar(
        user_id=UUID(str(uuid4())),
        name="Test Calendar",
        auth_token_id=uuid4(),
        platform="outlook",
        platform_id="platform-id",
    )

    token = data_objects.AuthToken(
        id=calendar.auth_token_id,
        user_id=calendar.user_id,
        platform="outlook",
        token="token",
    )

    # Mock UOW methods
    allow(mock_calendar_repo).get(calendar.id).and_return(calendar)
    allow(mock_auth_token_repo).get(token.id).and_return(token)

    service = CalendarService(
        user=test_user,
        uow_factory=mock_uow_factory,
        google_gateway=mock_google_gateway,
    )

    with pytest.raises(NotImplementedError) as exc_info:
        await service.sync(calendar)
    assert "outlook" in str(exc_info.value)




@pytest.mark.asyncio
async def test_sync_all_successful_syncs(
    test_user,
    mock_auth_token_repo,
    mock_calendar_repo,
    mock_calendar_entry_repo,
    mock_google_gateway,
    mock_uow_factory,
    test_datetime_noon,
):
    """Test syncing all calendars with successful syncs."""
    calendar1 = Calendar(
        user_id=UUID(str(uuid4())),
        name="Calendar 1",
        auth_token_id=uuid4(),
        platform="google",
        platform_id="platform-id-1",
    )
    calendar2 = Calendar(
        user_id=UUID(str(uuid4())),
        name="Calendar 2",
        auth_token_id=uuid4(),
        platform="google",
        platform_id="platform-id-2",
    )

    token1 = data_objects.AuthToken(
        id=calendar1.auth_token_id,
        user_id=calendar1.user_id,
        platform="google",
        token="token1",
    )
    token2 = data_objects.AuthToken(
        id=calendar2.auth_token_id,
        user_id=calendar2.user_id,
        platform="google",
        token="token2",
    )

    calendar_entry1 = CalendarEntry(
        user_id=calendar1.user_id,
        name="Calendar Entry 1",
        frequency=TaskFrequency.ONCE,
        calendar_id=calendar1.id,
        platform_id="entry-id-1",
        platform="google",
        status="confirmed",
        starts_at=test_datetime_noon,
    )
    calendar_entry2 = CalendarEntry(
        user_id=calendar2.user_id,
        name="Calendar Entry 2",
        frequency=TaskFrequency.ONCE,
        calendar_id=calendar2.id,
        platform_id="entry-id-2",
        platform="google",
        status="confirmed",
        starts_at=test_datetime_noon,
    )

    allow(mock_calendar_repo).all().and_return([calendar1, calendar2])

    # First calendar
    allow(mock_auth_token_repo).get(token1.id).and_return(token1)
    allow(mock_google_gateway).load_calendar_events(
        calendar1,
        lookback=test_datetime_noon - timedelta(days=2),
        token=token1,
    ).and_return([calendar_entry1])

    # Second calendar
    allow(mock_auth_token_repo).get(token2.id).and_return(token2)
    allow(mock_google_gateway).load_calendar_events(
        calendar2,
        lookback=test_datetime_noon - timedelta(days=2),
        token=token2,
    ).and_return([calendar_entry2])

    allow(mock_calendar_entry_repo).put.and_return(None)
    allow(mock_calendar_entry_repo).delete.and_return(None)

    service = CalendarService(
        user=test_user,
        uow_factory=mock_uow_factory,
        google_gateway=mock_google_gateway,
    )

    await service.sync_all()

    # Verify both calendars were synced (last_sync_at should be set)
    assert calendar1.last_sync_at is not None
    assert calendar2.last_sync_at is not None


@pytest.mark.asyncio
async def test_sync_all_with_exception_during_sync(
    test_user,
    mock_auth_token_repo, mock_calendar_repo, mock_calendar_entry_repo, mock_google_gateway, mock_uow_factory
):
    """Test syncing all calendars handles exceptions during sync."""
    calendar1 = Calendar(
        user_id=UUID(str(uuid4())),
        name="Calendar 1",
        auth_token_id=uuid4(),
        platform="google",
        platform_id="platform-id-1",
    )
    calendar2 = Calendar(
        user_id=UUID(str(uuid4())),
        name="Calendar 2",
        auth_token_id=uuid4(),
        platform="google",
        platform_id="platform-id-2",
    )

    token1 = data_objects.AuthToken(
        id=calendar1.auth_token_id,
        user_id=calendar1.user_id,
        platform="google",
        token="token1",
    )
    token2 = data_objects.AuthToken(
        id=calendar2.auth_token_id,
        user_id=calendar2.user_id,
        platform="google",
        token="token2",
    )

    allow(mock_calendar_repo).all().and_return([calendar1, calendar2])

    # First calendar raises exception
    allow(mock_auth_token_repo).get(token1.id).and_raise(Exception("Sync error"))

    # Second calendar succeeds
    allow(mock_auth_token_repo).get(token2.id).and_return(token2)
    allow(mock_google_gateway).load_calendar_events.and_return([])
    allow(mock_calendar_entry_repo).put.and_return(None)

    service = CalendarService(
        user=test_user,
        uow_factory=mock_uow_factory,
        google_gateway=mock_google_gateway,
    )

    # Should handle errors gracefully and continue
    await service.sync_all()

    # Second calendar should still be synced
    assert calendar2.last_sync_at is not None
