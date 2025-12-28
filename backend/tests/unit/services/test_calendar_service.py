"""Unit tests for CalendarService."""

import datetime
from datetime import timedelta
from uuid import uuid4, UUID

import pytest
from dobles import allow

from planned.application.services import CalendarService
from planned.core.exceptions import exceptions
from planned.domain.entities import Calendar, Event


@pytest.mark.asyncio
async def test_sync_google(mock_auth_token_repo, mock_calendar_repo, mock_event_repo, mock_google_gateway):
    """Test syncing Google calendar."""
    from datetime import UTC
    
    calendar = Calendar(
        user_uuid=UUID(str(uuid4())),
        name="Test Calendar",
        auth_token_id="token-id",
        platform="google",
        platform_id="platform-id",
    )
    
    lookback = datetime.datetime.now(UTC) - timedelta(days=2)
    
    from planned.domain.entities import AuthToken
    token = AuthToken(
        id="token-id",
        user_uuid=calendar.user_uuid,
        platform="google",
        token="token",
    )
    
    event1 = Event(
        id=str(uuid4()),
        user_uuid=calendar.user_uuid,
        name="Event 1",
        frequency="ONCE",
        calendar_id=calendar.id,
        platform_id="event-id-1",
        platform="google",
        status="confirmed",
        starts_at=datetime.datetime.now(UTC),
    )
    event2 = Event(
        id=str(uuid4()),
        user_uuid=calendar.user_uuid,
        name="Event 2",
        frequency="ONCE",
        calendar_id=calendar.id,
        platform_id="event-id-2",
        platform="google",
        status="cancelled",
        starts_at=datetime.datetime.now(UTC),
    )
    
    allow(mock_auth_token_repo).get("token-id").and_return(token)
    allow(mock_google_gateway).load_calendar_events(
        calendar,
        lookback=lookback,
        token=token,
    ).and_return([event1, event2])
    allow(mock_event_repo).put.and_return(event1)
    allow(mock_event_repo).delete.and_return(None)
    
    service = CalendarService(
        auth_token_repo=mock_auth_token_repo,
        calendar_repo=mock_calendar_repo,
        event_repo=mock_event_repo,
        google_gateway=mock_google_gateway,
    )
    
    events, deleted_events = await service.sync_google(calendar, lookback)
    
    assert len(events) == 1
    assert len(deleted_events) == 1
    assert events[0].name == "Event 1"
    assert deleted_events[0].name == "Event 2"


@pytest.mark.asyncio
async def test_sync(mock_auth_token_repo, mock_calendar_repo, mock_event_repo, mock_google_gateway):
    """Test syncing a calendar."""
    from datetime import UTC
    
    calendar = Calendar(
        user_uuid=UUID(str(uuid4())),
        name="Test Calendar",
        auth_token_id="token-id",
        platform="google",
        platform_id="platform-id",
    )
    
    from planned.domain.entities import AuthToken
    token = AuthToken(
        id="token-id",
        user_uuid=calendar.user_uuid,
        platform="google",
        token="token",
    )
    
    event = Event(
        id=str(uuid4()),
        user_uuid=calendar.user_uuid,
        name="Event",
        frequency="ONCE",
        calendar_id=calendar.id,
        platform_id="event-id",
        platform="google",
        status="confirmed",
        starts_at=datetime.datetime.now(UTC),
    )
    
    allow(mock_auth_token_repo).get("token-id").and_return(token)
    allow(mock_google_gateway).load_calendar_events.and_return([event])
    allow(mock_event_repo).put.and_return(event)
    
    service = CalendarService(
        auth_token_repo=mock_auth_token_repo,
        calendar_repo=mock_calendar_repo,
        event_repo=mock_event_repo,
        google_gateway=mock_google_gateway,
    )
    
    events, deleted_events = await service.sync(calendar)
    
    assert len(events) == 1
    assert calendar.last_sync_at is not None


@pytest.mark.asyncio
async def test_sync_all(mock_auth_token_repo, mock_calendar_repo, mock_event_repo, mock_google_gateway):
    """Test syncing all calendars."""
    from datetime import UTC
    
    calendar1 = Calendar(
        user_uuid=UUID(str(uuid4())),
        name="Calendar 1",
        auth_token_id="token-id-1",
        platform="google",
        platform_id="platform-id-1",
    )
    calendar2 = Calendar(
        user_uuid=UUID(str(uuid4())),
        name="Calendar 2",
        auth_token_id="token-id-2",
        platform="google",
        platform_id="platform-id-2",
    )
    
    allow(mock_calendar_repo).all().and_return([calendar1, calendar2])
    allow(mock_auth_token_repo).get.and_raise(exceptions.TokenExpiredError("Token expired"))
    allow(mock_event_repo).put.and_return(None)
    
    service = CalendarService(
        auth_token_repo=mock_auth_token_repo,
        calendar_repo=mock_calendar_repo,
        event_repo=mock_event_repo,
        google_gateway=mock_google_gateway,
    )
    
    # Should handle errors gracefully
    await service.sync_all()

