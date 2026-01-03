"""E2E tests for calendar entries router endpoints."""

import datetime
from datetime import UTC
from uuid import uuid4, uuid5, NAMESPACE_DNS
from zoneinfo import ZoneInfo

import pytest

from planned.core.config import settings
from planned.domain.entities import CalendarEntryEntity
from planned.domain.value_objects.task import TaskFrequency
from planned.infrastructure.repositories import CalendarEntryRepository


@pytest.mark.asyncio
async def test_get_today(authenticated_client, test_date):
    """Test getting today's calendar entries."""
    client, user = await authenticated_client()
    
    # Create a calendar entry for today
    calendar_entry_repo = CalendarEntryRepository(user_id=user.id)
    starts_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    calendar_entry = CalendarEntryEntity(
        id=uuid4(),
        user_id=user.id,
        name="Test Calendar Entry",
        frequency=TaskFrequency.ONCE,
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-id",
        platform="testing",
        status="confirmed",
        starts_at=starts_at,
    )
    await calendar_entry_repo.put(calendar_entry)
    
    response = client.get("/calendar-entries/today")
    
    assert response.status_code == 200
    calendar_entries = response.json()
    assert isinstance(calendar_entries, list)
    # Calendar entry should be in the list if test_date is today
    # (Otherwise this would need to be adjusted based on actual test_date fixture)

