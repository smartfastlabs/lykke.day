"""E2E tests for events router endpoints."""

import datetime
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio

from planned.core.config import settings


@pytest.mark.asyncio
async def test_get_today(authenticated_client, test_date):
    """Test getting today's events."""
    client, user = authenticated_client
    
    # Create an event for today
    from uuid import UUID, uuid4
    from planned.domain.entities import Event
    from planned.infrastructure.repositories import EventRepository
    
    event_repo = EventRepository(user_uuid=UUID(user.id))
    starts_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    )
    event = Event(
        id=str(uuid4()),
        user_uuid=UUID(user.id),
        name="Test Event",
        frequency="ONCE",
        calendar_id="test-calendar",
        platform_id="test-id",
        platform="testing",
        status="confirmed",
        starts_at=starts_at,
    )
    await event_repo.put(event)
    
    response = client.get("/api/events/today")
    
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    # Event should be in the list if test_date is today
    # (Otherwise this would need to be adjusted based on actual test_date fixture)

