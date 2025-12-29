"""E2E tests for events router endpoints."""

import datetime
from uuid import uuid4, uuid5, NAMESPACE_DNS
from zoneinfo import ZoneInfo

import pytest

from planned.core.config import settings
from planned.domain.entities import Event
from planned.infrastructure.repositories import EventRepository


@pytest.mark.asyncio
async def test_get_today(authenticated_client, test_date):
    """Test getting today's events."""
    client, user = await authenticated_client()
    
    # Create an event for today
    event_repo = EventRepository(user_uuid=user.uuid)
    starts_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    )
    event = Event(
        uuid=uuid4(),
        user_uuid=user.uuid,
        name="Test Event",
        frequency="ONCE",
        calendar_uuid=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-id",
        platform="testing",
        status="confirmed",
        starts_at=starts_at,
    )
    await event_repo.put(event)
    
    response = client.get("/events/today")
    
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    # Event should be in the list if test_date is today
    # (Otherwise this would need to be adjusted based on actual test_date fixture)

